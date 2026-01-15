#!/usr/bin/env python3
"""
LLM Bridge Main Server
Integrates all components: WebSocket bridge, LLM interpreter, music logic, and validator
"""

import asyncio
import json
import logging
import os
import sys
from typing import Optional, Dict, List
from pathlib import Path

import websockets
from websockets.server import WebSocketServerProtocol

from bridge_server import MuseScoreBridge, AtomicCommand
from llm_interpreter import LLMInterpreter, interpreter
from music_logic import MusicGenerator
from validator import CommandValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LLMBridgeServer:
    """Main server that orchestrates everything"""

    def __init__(self):
        self.bridge = MuseScoreBridge(port=8766)
        self.interpreter = interpreter
        self.validator: Optional[CommandValidator] = None
        self.generator: Optional[MusicGenerator] = None

        # Load config
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load configuration from file or environment"""
        config_path = Path(__file__).parent / "config.json"
        config = {
            "provider": os.environ.get("LLM_PROVIDER", "claude"),
            "api_key": os.environ.get("LLM_API_KEY", ""),
            "model": os.environ.get("LLM_MODEL", ""),
        }

        if config_path.exists():
            with open(config_path) as f:
                file_config = json.load(f)
                config.update(file_config)

        return config

    def configure_llm(self, provider: str, api_key: str, model: str = None):
        """Configure the LLM provider"""
        self.interpreter.set_provider(provider, api_key, model)
        logger.info(f"LLM configured: {provider}")

    async def process_request(self, user_request: str) -> Dict:
        """
        Process a natural language request

        Args:
            user_request: User's natural language request

        Returns:
            Result dictionary with status and details
        """
        result = {
            "success": False,
            "intent": "",
            "commands_sent": 0,
            "errors": [],
            "notes": ""
        }

        try:
            # Get current score context
            score_context = None
            if self.bridge.score_info:
                score_context = {
                    "title": self.bridge.score_info.title,
                    "measures": self.bridge.score_info.measures,
                    "staves": self.bridge.score_info.staves,
                    "time_signature": self.bridge.score_info.time_signature,
                    "key_signature": self.bridge.score_info.key_signature,
                    "parts": self.bridge.score_info.parts
                }

            # Interpret the request via LLM
            llm_response = await self.interpreter.interpret(user_request, score_context)
            result["intent"] = llm_response.intent
            result["notes"] = llm_response.notes

            if not llm_response.commands:
                result["errors"].append("No commands generated")
                return result

            # Validate commands
            if score_context:
                self.validator = CommandValidator(score_context)
            else:
                self.validator = CommandValidator()

            valid_commands, validation_errors = self.validator.validate_commands(llm_response.commands)
            result["errors"].extend(validation_errors)

            if not valid_commands:
                result["errors"].append("No valid commands after validation")
                return result

            # Send commands to MuseScore
            commands = [AtomicCommand(cmd["type"], cmd) for cmd in valid_commands]
            success = await self.bridge.send_commands(commands)

            if success:
                result["success"] = True
                result["commands_sent"] = len(valid_commands)
            else:
                result["errors"].append("Failed to send commands to MuseScore")

        except Exception as e:
            logger.exception("Error processing request")
            result["errors"].append(str(e))

        return result

    async def process_music_logic(self, action: str, params: Dict) -> Dict:
        """
        Process using Music21 logic instead of LLM

        Args:
            action: Action type (walking_bass, drum_pattern, etc.)
            params: Action parameters

        Returns:
            Result dictionary
        """
        result = {"success": False, "errors": [], "commands_sent": 0}

        try:
            # Initialize generator with current score context
            time_sig = (4, 4)
            key = "C"

            if self.bridge.score_info:
                if self.bridge.score_info.time_signature:
                    time_sig = (
                        self.bridge.score_info.time_signature.get("numerator", 4),
                        self.bridge.score_info.time_signature.get("denominator", 4)
                    )
                if self.bridge.score_info.key_signature is not None:
                    # Convert key signature number to key name
                    key_map = {
                        -7: "Cb", -6: "Gb", -5: "Db", -4: "Ab", -3: "Eb", -2: "Bb", -1: "F",
                        0: "C", 1: "G", 2: "D", 3: "A", 4: "E", 5: "B", 6: "F#", 7: "C#"
                    }
                    key = key_map.get(self.bridge.score_info.key_signature, "C")

            self.generator = MusicGenerator(key_signature=key, time_signature=time_sig)

            # Generate commands based on action
            commands = []

            if action == "walking_bass":
                chords = params.get("chords", ["C", "F", "G", "C"])
                measures = params.get("measures", 4)
                commands = self.generator.walking_bass_line(chords, measures)

            elif action == "drum_pattern":
                style = params.get("style", "rock")
                measures = params.get("measures", 4)
                commands = self.generator.drum_pattern(style, measures)

            else:
                result["errors"].append(f"Unknown action: {action}")
                return result

            # Validate and send
            self.validator = CommandValidator(
                {"measures": self.bridge.score_info.measures if self.bridge.score_info else 100}
            )
            valid_commands, errors = self.validator.validate_commands(commands)
            result["errors"].extend(errors)

            if valid_commands:
                atomic_commands = [AtomicCommand(cmd["type"], cmd) for cmd in valid_commands]
                success = await self.bridge.send_commands(atomic_commands)
                if success:
                    result["success"] = True
                    result["commands_sent"] = len(valid_commands)

        except Exception as e:
            logger.exception("Error in music logic")
            result["errors"].append(str(e))

        return result

    async def run_cli(self):
        """Run interactive CLI"""
        print("\n" + "=" * 60)
        print("LLM Bridge Server - Interactive Mode")
        print("=" * 60)
        print("\nCommands:")
        print("  <text>     - Send natural language request to LLM")
        print("  /bass      - Generate walking bass (Music21)")
        print("  /drums     - Generate drum pattern (Music21)")
        print("  /info      - Show current score info")
        print("  /ping      - Ping MuseScore plugin")
        print("  /quit      - Exit")
        print("\n")

        while True:
            try:
                user_input = input(">>> ").strip()

                if not user_input:
                    continue

                if user_input == "/quit":
                    print("Goodbye!")
                    break

                elif user_input == "/info":
                    if self.bridge.score_info:
                        print(f"Score: {self.bridge.score_info.title}")
                        print(f"  Measures: {self.bridge.score_info.measures}")
                        print(f"  Staves: {self.bridge.score_info.staves}")
                        print(f"  Time: {self.bridge.score_info.time_signature}")
                    else:
                        print("No score info available")

                elif user_input == "/ping":
                    success = await self.bridge.ping()
                    print("Ping sent" if success else "Not connected")

                elif user_input == "/bass":
                    chords = input("Chords (e.g., G C D G): ").strip().split()
                    measures = int(input("Measures: ").strip() or "4")
                    result = await self.process_music_logic("walking_bass", {
                        "chords": chords,
                        "measures": measures
                    })
                    print(f"Result: {result}")

                elif user_input == "/drums":
                    style = input("Style (rock/jazz/pop/latin/metal): ").strip() or "rock"
                    measures = int(input("Measures: ").strip() or "4")
                    result = await self.process_music_logic("drum_pattern", {
                        "style": style,
                        "measures": measures
                    })
                    print(f"Result: {result}")

                else:
                    # Natural language request
                    print("Processing...")
                    result = await self.process_request(user_input)
                    print(f"\nIntent: {result['intent']}")
                    print(f"Commands sent: {result['commands_sent']}")
                    if result['errors']:
                        print(f"Errors: {result['errors']}")
                    if result['notes']:
                        print(f"Notes: {result['notes']}")
                    print()

            except KeyboardInterrupt:
                print("\nUse /quit to exit")
            except Exception as e:
                print(f"Error: {e}")

    async def start(self):
        """Start the server"""
        # Configure LLM if API key is available
        if self.config.get("api_key"):
            self.configure_llm(
                self.config.get("provider", "claude"),
                self.config["api_key"],
                self.config.get("model")
            )
        else:
            logger.warning("No API key configured. Set LLM_API_KEY environment variable.")

        # Start WebSocket server in background
        server_task = asyncio.create_task(self.bridge.start_server())

        # Wait a moment for server to start
        await asyncio.sleep(0.5)
        print(f"\nWebSocket server running on ws://localhost:8766")
        print("Waiting for MuseScore plugin to connect...")

        # Run CLI
        await self.run_cli()

        # Cleanup
        server_task.cancel()


async def main():
    """Main entry point"""
    server = LLMBridgeServer()
    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
