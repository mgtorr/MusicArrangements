#!/usr/bin/env python3
"""
LLM Bridge server.

MuseScore's plugin polls this process over HTTP. A small desk page on
http://localhost:8766 sends the same commands without using the terminal.
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

CONSOLE_PATH = Path(__file__).with_name("console.html")
MAX_BODY = 1_000_000


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"


@dataclass
class ScoreInfo:
    title: str = ""
    composer: str = ""
    measures: int = 0
    staves: int = 0
    parts: List[Dict] = None
    time_signature: Optional[Dict] = None
    key_signature: Optional[int] = None
    tempo: Optional[int] = None

    def __post_init__(self):
        if self.parts is None:
            self.parts = []


@dataclass
class AtomicCommand:
    type: str
    params: Dict[str, Any] = None

    def __post_init__(self):
        if self.params is None:
            self.params = {}

    def to_dict(self) -> Dict:
        result = {"type": self.type}
        result.update(self.params)
        # `type` in params must not be able to rename the command.
        result["type"] = self.type
        return result


@dataclass
class Delivery:
    batch_id: int
    queued: bool
    confirmed: bool
    failed: int = 0
    errors: List[str] = field(default_factory=list)


class MuseScoreBridge:
    """HTTP bridge between this process and the MuseScore plugin."""

    def __init__(self, host: str = "localhost", port: int = 8766):
        self.host = host
        self.port = port
        self.state = ConnectionState.DISCONNECTED
        self.score_info: Optional[ScoreInfo] = None
        self.pending_commands: List[Dict] = []
        self.last_results: Dict = {}
        self.results_by_batch: Dict[int, Dict] = {}
        self.command_id = 0
        self.last_seen = 0.0
        self._waiters: Dict[int, asyncio.Event] = {}
        self._tcp = None
        self.on_request: Optional[Callable] = None
        self.on_music: Optional[Callable] = None
        self.llm_status: Optional[Callable] = None

    async def start_server(self):
        self._tcp = await asyncio.start_server(self._handle_connection, self.host, self.port)
        sockets = self._tcp.sockets or []
        if sockets:
            self.port = sockets[0].getsockname()[1]
        logger.info("LLM Bridge listening on http://%s:%s", self.host, self.port)
        async with self._tcp:
            await self._tcp.serve_forever()

    def plugin_connected(self, within: float = 5.0) -> bool:
        if not self.last_seen:
            return False
        return (time.monotonic() - self.last_seen) <= within

    def mark_plugin_seen(self):
        self.last_seen = time.monotonic()
        self.state = ConnectionState.CONNECTED

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        restore: List[Dict] = []
        try:
            request_line = await reader.readline()
            if not request_line:
                return
            parts = request_line.decode("utf-8", errors="replace").strip().split(" ")
            if len(parts) < 2:
                return
            method, path = parts[0], parts[1]

            headers = {}
            content_length = 0
            while True:
                line = await reader.readline()
                if line in (b"\r\n", b"\n", b""):
                    break
                decoded = line.decode("utf-8", errors="replace").strip()
                if ":" not in decoded:
                    continue
                key, value = decoded.split(":", 1)
                headers[key.strip().lower()] = value.strip()
                if key.strip().lower() == "content-length":
                    content_length = int(value.strip() or "0")

            body = b""
            if content_length > 0:
                if content_length > MAX_BODY:
                    writer.write(_json_bytes(413, {"status": "error", "message": "Request is too large"}))
                    await writer.drain()
                    return
                body = await reader.readexactly(content_length)

            response, restore = await self._route_request(method, path, body)
            writer.write(response)
            await writer.drain()
            restore = []
        except asyncio.IncompleteReadError:
            logger.warning("Client closed the connection before the body arrived")
        except Exception as exc:
            logger.error("Error handling request: %s", exc)
            try:
                writer.write(_json_bytes(500, {"status": "error", "message": "Internal error"}))
                await writer.drain()
            except Exception:
                pass
        finally:
            if restore:
                self.pending_commands = restore + self.pending_commands
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def _route_request(self, method: str, path: str, body: bytes):
        route = path.split("?", 1)[0]
        if len(route) > 1 and route.endswith("/"):
            route = route.rstrip("/")

        if method == "OPTIONS":
            return _empty(200), []
        if method == "GET" and route in ("", "/"):
            return _html_bytes(_console_html()), []
        if method == "GET" and route == "/ping":
            self.mark_plugin_seen()
            return _json_bytes(200, {"status": "ok", "version": "2.1.0"}), []
        if method == "GET" and route == "/poll":
            self.mark_plugin_seen()
            commands = self.pending_commands
            self.pending_commands = []
            return _json_bytes(200, {"commands": commands}), commands
        if method == "GET" and route == "/status":
            return _json_bytes(200, self.status_payload()), []
        if method == "POST" and route == "/score_info":
            self.mark_plugin_seen()
            return self._read_score(body), []
        if method == "POST" and route == "/results":
            self.mark_plugin_seen()
            return self._read_results(body), []
        if method == "POST" and route == "/request":
            return await self._read_request(body), []
        if method == "POST" and route == "/music":
            return await self._read_music(body), []
        return _json_bytes(404, {"status": "error", "message": "Not found"}), []

    def status_payload(self) -> Dict[str, Any]:
        score = None
        if self.score_info:
            score = asdict(self.score_info)
            if score.get("key_signature") is not None:
                from music_logic import key_signature_name
                score["key_name"] = key_signature_name(score["key_signature"])
        llm = {"configured": False, "provider": "", "model": ""}
        if self.llm_status:
            try:
                llm = self.llm_status() or llm
            except Exception:
                logger.exception("Could not read model status")
        return {
            "version": "2.1.0",
            "plugin_connected": self.plugin_connected(),
            "pending_commands": len(self.pending_commands),
            "score": score,
            "last_results": self.last_results,
            "llm": llm,
        }

    def _read_score(self, body: bytes) -> bytes:
        try:
            data = json.loads(body.decode("utf-8"))
        except Exception as exc:
            return _json_bytes(400, {"status": "error", "message": str(exc)})
        self._update_score_info(data)
        return _json_bytes(200, {"status": "ok"})

    def _read_results(self, body: bytes) -> bytes:
        try:
            data = json.loads(body.decode("utf-8"))
        except Exception as exc:
            return _json_bytes(400, {"status": "error", "message": str(exc)})
        self.last_results = data
        batch_ids = list(data.get("batch_ids") or [])
        if data.get("batch_id") is not None:
            batch_ids.append(data["batch_id"])
        for batch_id in batch_ids:
            try:
                key = int(batch_id)
            except (TypeError, ValueError):
                continue
            self.results_by_batch[key] = data
            waiter = self._waiters.get(key)
            if waiter:
                waiter.set()
        logger.info(
            "Plugin applied %s command(s), %s failed",
            data.get("executed", 0),
            data.get("failed", 0),
        )
        return _json_bytes(200, {"status": "ok"})

    async def _read_request(self, body: bytes) -> bytes:
        try:
            data = json.loads(body.decode("utf-8")) if body else {}
        except Exception as exc:
            return _json_bytes(400, {"status": "error", "message": str(exc)})
        text = str(data.get("request") or data.get("text") or "").strip()
        if not text:
            return _json_bytes(400, {"success": False, "status": "invalid", "errors": ["Write a request first."]})
        if not self.on_request:
            return _json_bytes(500, {"success": False, "status": "error", "errors": ["Server is not ready."]})
        try:
            result = await self.on_request(text)
        except Exception as exc:
            logger.exception("Request failed")
            return _json_bytes(500, {"success": False, "status": "error", "errors": [str(exc)]})
        return _json_bytes(200, result)

    async def _read_music(self, body: bytes) -> bytes:
        try:
            data = json.loads(body.decode("utf-8")) if body else {}
        except Exception as exc:
            return _json_bytes(400, {"status": "error", "message": str(exc)})
        if not self.on_music:
            return _json_bytes(500, {"success": False, "status": "error", "errors": ["Server is not ready."]})
        try:
            result = await self.on_music(str(data.get("action") or ""), data)
        except Exception as exc:
            logger.exception("Music request failed")
            return _json_bytes(500, {"success": False, "status": "error", "errors": [str(exc)]})
        return _json_bytes(200, result)

    def _update_score_info(self, data: Optional[Dict]):
        if not data:
            self.score_info = None
            logger.info("No score open")
            return
        self.score_info = ScoreInfo(
            title=data.get("title", ""),
            composer=data.get("composer", ""),
            measures=data.get("measures", 0),
            staves=data.get("staves", 0),
            parts=data.get("parts", []),
            time_signature=data.get("timeSignature"),
            key_signature=data.get("keySignature"),
            tempo=data.get("tempo"),
        )
        logger.info("Score loaded: %s (%s bars)", self.score_info.title, self.score_info.measures)

    async def send_commands(self, commands: List[AtomicCommand], wait: bool = False, timeout: float = 8.0) -> Delivery:
        batch_id = self.command_id
        self.command_id += 1
        payload = []
        for command in commands:
            item = command.to_dict()
            item["batch_id"] = batch_id
            payload.append(item)

        event = asyncio.Event()
        if wait:
            self._waiters[batch_id] = event
        self.pending_commands.extend(payload)
        logger.info("Queued %s command(s) as batch %s", len(payload), batch_id)

        if not wait:
            return Delivery(batch_id=batch_id, queued=True, confirmed=False)

        confirmed = False
        try:
            await asyncio.wait_for(event.wait(), timeout)
            confirmed = True
        except asyncio.TimeoutError:
            confirmed = False
        finally:
            self._waiters.pop(batch_id, None)

        report = self.results_by_batch.pop(batch_id, {})
        errors = [str(item) for item in (report.get("errors") or [])]
        failed = int(report.get("failed") or 0)
        return Delivery(
            batch_id=batch_id,
            queued=True,
            confirmed=confirmed,
            failed=failed,
            errors=errors,
        )

    async def send_command(self, command: AtomicCommand) -> bool:
        delivery = await self.send_commands([command])
        return delivery.queued

    def queue_command(self, command: AtomicCommand):
        self.pending_commands.append(command.to_dict())

    def queue_commands(self, commands: List[AtomicCommand]):
        for command in commands:
            self.pending_commands.append(command.to_dict())

    def create_add_note(self, pitch: int, duration: int = 480, measure: int = 0, track: int = 0) -> AtomicCommand:
        return AtomicCommand("add_note", {
            "pitch": pitch,
            "duration": duration,
            "measure": measure,
            "tick": 0,
            "track": track,
        })

    def create_add_chord(self, pitches: List[int], duration: int = 480, measure: int = 0, track: int = 0) -> AtomicCommand:
        return AtomicCommand("add_chord", {
            "pitches": pitches,
            "duration": duration,
            "measure": measure,
            "tick": 0,
            "track": track,
        })

    def create_add_rest(self, duration: int = 480, measure: int = 0, track: int = 0) -> AtomicCommand:
        return AtomicCommand("add_rest", {
            "duration": duration,
            "measure": measure,
            "tick": 0,
            "track": track,
        })

    def create_add_dynamic(self, dynamic: str, measure: int = 0, track: int = 0) -> AtomicCommand:
        return AtomicCommand("add_dynamic", {"dynamic": dynamic, "measure": measure, "track": track})

    def create_add_tempo(self, bpm: int, measure: int = 0, text: str = None) -> AtomicCommand:
        params = {"bpm": bpm, "measure": measure}
        if text:
            params["text"] = text
        return AtomicCommand("add_tempo", params)


def _console_html() -> bytes:
    if CONSOLE_PATH.exists():
        return CONSOLE_PATH.read_bytes()
    return b"<!doctype html><title>LLM Bridge</title><p>The desk page is missing.</p>"


def _json_bytes(status: int, payload: Dict) -> bytes:
    body = json.dumps(payload).encode("utf-8")
    reason = {200: "OK", 400: "Bad Request", 404: "Not Found", 413: "Payload Too Large", 500: "Internal Server Error"}.get(status, "OK")
    head = (
        f"HTTP/1.1 {status} {reason}\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        "Access-Control-Allow-Headers: Content-Type\r\n"
        "Content-Type: application/json; charset=utf-8\r\n"
        "Cache-Control: no-store\r\n"
        "Connection: close\r\n"
        f"Content-Length: {len(body)}\r\n"
        "\r\n"
    )
    return head.encode("ascii") + body


def _html_bytes(body: bytes) -> bytes:
    head = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "Cache-Control: no-store\r\n"
        "Connection: close\r\n"
        f"Content-Length: {len(body)}\r\n"
        "\r\n"
    )
    return head.encode("ascii") + body


def _empty(status: int) -> bytes:
    reason = "OK" if status == 200 else "No Content"
    head = (
        f"HTTP/1.1 {status} {reason}\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        "Access-Control-Allow-Headers: Content-Type\r\n"
        "Content-Length: 0\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    return head.encode("ascii")


bridge = MuseScoreBridge()


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    await bridge.start_server()


if __name__ == "__main__":
    asyncio.run(main())
