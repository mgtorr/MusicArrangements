#!/usr/bin/env python3
"""
LLM Bridge Server - The "Brain" middleware
Connects to MuseScore plugin via HTTP polling
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum
from http.server import BaseHTTPRequestHandler
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"


@dataclass
class ScoreInfo:
    """Current score information from MuseScore"""
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
    """A single atomic command for MuseScore"""
    type: str
    params: Dict[str, Any] = None

    def __post_init__(self):
        if self.params is None:
            self.params = {}

    def to_dict(self) -> Dict:
        result = {"type": self.type}
        result.update(self.params)
        return result


class MuseScoreBridge:
    """Bridge between LLM and MuseScore plugin via HTTP"""

    def __init__(self, host: str = "localhost", port: int = 8766):
        self.host = host
        self.port = port
        self.state = ConnectionState.DISCONNECTED
        self.score_info: Optional[ScoreInfo] = None
        self.pending_commands: List[Dict] = []
        self.last_results: Dict = {}
        self.command_id = 0

    async def start_server(self):
        """Start the HTTP server"""
        server = await asyncio.start_server(
            self._handle_connection,
            self.host,
            self.port
        )
        logger.info(f"Starting LLM Bridge HTTP Server on http://{self.host}:{self.port}")
        async with server:
            await server.serve_forever()

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming HTTP connection"""
        try:
            # Read request line
            request_line = await reader.readline()
            if not request_line:
                return

            request_line = request_line.decode('utf-8').strip()
            parts = request_line.split(' ')
            if len(parts) < 2:
                return

            method = parts[0]
            path = parts[1]

            # Read headers
            headers = {}
            content_length = 0
            while True:
                line = await reader.readline()
                if line == b'\r\n' or line == b'\n' or not line:
                    break
                line = line.decode('utf-8').strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()
                    if key.strip().lower() == 'content-length':
                        content_length = int(value.strip())

            # Read body if present
            body = b''
            if content_length > 0:
                body = await reader.read(content_length)

            # Route request
            response = await self._route_request(method, path, body, headers)

            # Send response
            writer.write(response.encode('utf-8'))
            await writer.drain()

        except Exception as e:
            logger.error(f"Error handling request: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def _route_request(self, method: str, path: str, body: bytes, headers: Dict) -> str:
        """Route HTTP request to appropriate handler"""

        # CORS headers for all responses
        cors_headers = (
            "Access-Control-Allow-Origin: *\r\n"
            "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
            "Access-Control-Allow-Headers: Content-Type\r\n"
        )

        # Handle CORS preflight
        if method == "OPTIONS":
            return f"HTTP/1.1 200 OK\r\n{cors_headers}Content-Length: 0\r\n\r\n"

        if method == "GET" and path == "/ping":
            return self._handle_ping(cors_headers)

        elif method == "GET" and path == "/poll":
            return self._handle_poll(cors_headers)

        elif method == "POST" and path == "/score_info":
            return await self._handle_score_info(body, cors_headers)

        elif method == "POST" and path == "/results":
            return self._handle_results(body, cors_headers)

        else:
            return f"HTTP/1.1 404 Not Found\r\n{cors_headers}Content-Length: 0\r\n\r\n"

    def _handle_ping(self, cors_headers: str) -> str:
        """Handle ping request - used for connection check"""
        self.state = ConnectionState.CONNECTED
        response_body = json.dumps({"status": "ok", "version": "2.0.0"})
        return (
            f"HTTP/1.1 200 OK\r\n"
            f"{cors_headers}"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(response_body)}\r\n"
            f"\r\n"
            f"{response_body}"
        )

    def _handle_poll(self, cors_headers: str) -> str:
        """Handle poll request - return pending commands"""
        commands = self.pending_commands.copy()
        self.pending_commands.clear()

        response_body = json.dumps({"commands": commands})
        return (
            f"HTTP/1.1 200 OK\r\n"
            f"{cors_headers}"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(response_body)}\r\n"
            f"\r\n"
            f"{response_body}"
        )

    async def _handle_score_info(self, body: bytes, cors_headers: str) -> str:
        """Handle score_info POST - receive score info from plugin"""
        try:
            data = json.loads(body.decode('utf-8'))
            self._update_score_info(data)
            response_body = json.dumps({"status": "ok"})
            return (
                f"HTTP/1.1 200 OK\r\n"
                f"{cors_headers}"
                f"Content-Type: application/json\r\n"
                f"Content-Length: {len(response_body)}\r\n"
                f"\r\n"
                f"{response_body}"
            )
        except Exception as e:
            logger.error(f"Error parsing score info: {e}")
            response_body = json.dumps({"status": "error", "message": str(e)})
            return (
                f"HTTP/1.1 400 Bad Request\r\n"
                f"{cors_headers}"
                f"Content-Type: application/json\r\n"
                f"Content-Length: {len(response_body)}\r\n"
                f"\r\n"
                f"{response_body}"
            )

    def _handle_results(self, body: bytes, cors_headers: str) -> str:
        """Handle results POST - receive execution results from plugin"""
        try:
            data = json.loads(body.decode('utf-8'))
            self.last_results = data
            logger.info(f"Received results: {data}")
            response_body = json.dumps({"status": "ok"})
            return (
                f"HTTP/1.1 200 OK\r\n"
                f"{cors_headers}"
                f"Content-Type: application/json\r\n"
                f"Content-Length: {len(response_body)}\r\n"
                f"\r\n"
                f"{response_body}"
            )
        except Exception as e:
            response_body = json.dumps({"status": "error", "message": str(e)})
            return (
                f"HTTP/1.1 400 Bad Request\r\n"
                f"{cors_headers}"
                f"Content-Type: application/json\r\n"
                f"Content-Length: {len(response_body)}\r\n"
                f"\r\n"
                f"{response_body}"
            )

    def _update_score_info(self, data: Optional[Dict]):
        """Update cached score information"""
        if data:
            self.score_info = ScoreInfo(
                title=data.get("title", ""),
                composer=data.get("composer", ""),
                measures=data.get("measures", 0),
                staves=data.get("staves", 0),
                parts=data.get("parts", []),
                time_signature=data.get("timeSignature"),
                key_signature=data.get("keySignature"),
                tempo=data.get("tempo")
            )
            logger.info(f"Score loaded: {self.score_info.title} ({self.score_info.measures} measures)")
        else:
            self.score_info = None
            logger.info("No score open")

    def queue_command(self, command: AtomicCommand):
        """Queue a command to be sent to MuseScore on next poll"""
        self.pending_commands.append(command.to_dict())
        logger.info(f"Queued command: {command.type}")

    def queue_commands(self, commands: List[AtomicCommand]):
        """Queue multiple commands"""
        for cmd in commands:
            self.pending_commands.append(cmd.to_dict())
        logger.info(f"Queued {len(commands)} commands")

    async def send_command(self, command: AtomicCommand) -> bool:
        """Queue a single command (for compatibility with old API)"""
        self.queue_command(command)
        return True

    async def send_commands(self, commands: List[AtomicCommand]) -> bool:
        """Queue a batch of commands (for compatibility with old API)"""
        self.queue_commands(commands)
        return True

    # === HIGH-LEVEL COMMANDS ===

    def create_add_note(self, pitch: int, duration: int = 480,
                        measure: int = 0, track: int = 0) -> AtomicCommand:
        """Create an add_note command"""
        return AtomicCommand("add_note", {
            "pitch": pitch,
            "duration": duration,
            "measure": measure,
            "track": track
        })

    def create_add_chord(self, pitches: List[int], duration: int = 480,
                         measure: int = 0, track: int = 0) -> AtomicCommand:
        """Create an add_chord command"""
        return AtomicCommand("add_chord", {
            "pitches": pitches,
            "duration": duration,
            "measure": measure,
            "track": track
        })

    def create_add_rest(self, duration: int = 480,
                        measure: int = 0, track: int = 0) -> AtomicCommand:
        """Create an add_rest command"""
        return AtomicCommand("add_rest", {
            "duration": duration,
            "measure": measure,
            "track": track
        })

    def create_add_dynamic(self, dynamic: str, measure: int = 0,
                           track: int = 0) -> AtomicCommand:
        """Create an add_dynamic command"""
        return AtomicCommand("add_dynamic", {
            "dynamic": dynamic,
            "measure": measure,
            "track": track
        })

    def create_add_tempo(self, bpm: int, measure: int = 0,
                         text: str = None) -> AtomicCommand:
        """Create an add_tempo command"""
        params = {"bpm": bpm, "measure": measure}
        if text:
            params["text"] = text
        return AtomicCommand("add_tempo", params)


# Singleton instance
bridge = MuseScoreBridge()


async def main():
    """Main entry point"""
    await bridge.start_server()


if __name__ == "__main__":
    asyncio.run(main())
