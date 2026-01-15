#!/usr/bin/env python3
"""
LLM Bridge Server - The "Brain" middleware
Connects to MuseScore plugin via WebSocket and processes LLM requests
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

import websockets
from websockets.server import WebSocketServerProtocol

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
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
    """Bridge between LLM and MuseScore plugin"""

    def __init__(self, host: str = "localhost", port: int = 8766):
        self.host = host
        self.port = port
        self.state = ConnectionState.DISCONNECTED
        self.musescore_ws: Optional[WebSocketServerProtocol] = None
        self.score_info: Optional[ScoreInfo] = None
        self.pending_responses: Dict[str, asyncio.Future] = {}
        self.command_id = 0

    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting LLM Bridge Server on ws://{self.host}:{self.port}")
        async with websockets.serve(self._handle_connection, self.host, self.port):
            await asyncio.Future()  # Run forever

    async def _handle_connection(self, websocket: WebSocketServerProtocol):
        """Handle incoming WebSocket connection from MuseScore plugin"""
        logger.info(f"New connection from {websocket.remote_address}")
        self.musescore_ws = websocket
        self.state = ConnectionState.CONNECTED

        try:
            async for message in websocket:
                await self._handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("MuseScore plugin disconnected")
        finally:
            self.musescore_ws = None
            self.state = ConnectionState.DISCONNECTED

    async def _handle_message(self, message: str):
        """Handle message from MuseScore plugin"""
        try:
            data = json.loads(message)
            msg_type = data.get("type", "")
            logger.debug(f"Received: {msg_type}")

            if msg_type == "handshake":
                logger.info(f"MuseScore plugin connected: v{data.get('version', '?')}")
                await self.request_score_info()

            elif msg_type == "score_info":
                self._update_score_info(data.get("data"))

            elif msg_type == "command_result":
                # Handle async command result
                pass

            elif msg_type == "pong":
                logger.debug("Pong received")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")

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

    async def send_command(self, command: AtomicCommand) -> bool:
        """Send a single command to MuseScore"""
        if not self.musescore_ws:
            logger.error("Not connected to MuseScore")
            return False

        try:
            await self.musescore_ws.send(json.dumps(command.to_dict()))
            return True
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            return False

    async def send_commands(self, commands: List[AtomicCommand]) -> bool:
        """Send a batch of commands to MuseScore"""
        if not self.musescore_ws:
            logger.error("Not connected to MuseScore")
            return False

        try:
            batch = {
                "type": "execute",
                "commands": [cmd.to_dict() for cmd in commands]
            }
            await self.musescore_ws.send(json.dumps(batch))
            return True
        except Exception as e:
            logger.error(f"Failed to send commands: {e}")
            return False

    async def request_score_info(self):
        """Request current score info from MuseScore"""
        if self.musescore_ws:
            await self.musescore_ws.send(json.dumps({"type": "get_score_info"}))

    async def ping(self) -> bool:
        """Ping the MuseScore plugin"""
        if self.musescore_ws:
            await self.musescore_ws.send(json.dumps({"type": "ping"}))
            return True
        return False

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
