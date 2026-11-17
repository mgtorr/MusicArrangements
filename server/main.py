#!/usr/bin/env python3
"""
LLM Bridge.

The MuseScore plugin and the desk page both talk to this process.
With an API key, a model interprets the sentence. Without one, the
local theory engine handles the common requests.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from bridge_server import AtomicCommand, MuseScoreBridge
from llm_interpreter import LLMInterpreter
from local_interpreter import interpret_locally
from music_logic import MusicGenerator, describe_command, key_signature_name
from validator import CommandValidator, order_commands

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

PLACEHOLDER_KEYS = {
    "",
    "YOUR_API_KEY_HERE",
    "your-api-key",
    "sk-ant-...",
    "AIza...",
    "sk-...",
}


def usable_api_key(value: Optional[str]) -> str:
    if not value or not isinstance(value, str):
        return ""
    stripped = value.strip()
    if stripped in PLACEHOLDER_KEYS or stripped.startswith("YOUR_"):
        return ""
    return stripped


class LLMBridgeServer:
    def __init__(self, host: str = "localhost", port: int = 8766):
        self.bridge = MuseScoreBridge(host=host, port=port)
        self.interpreter = LLMInterpreter()
        self.config = self._load_config()
        self.bridge.on_request = self.handle_request
        self.bridge.on_music = self.handle_music
        self.bridge.llm_status = self.llm_status

    def _load_config(self) -> Dict:
        config = {
            "provider": os.environ.get("LLM_PROVIDER", "claude"),
            "api_key": os.environ.get("LLM_API_KEY", ""),
            "model": os.environ.get("LLM_MODEL", ""),
        }
        config_path = Path(__file__).parent / "config.json"
        if config_path.exists():
            with open(config_path) as handle:
                config.update(json.load(handle))
        config["api_key"] = usable_api_key(config.get("api_key"))
        return config

    def configure_llm(self, provider: str, api_key: str, model: str = None):
        self.interpreter.set_provider(provider, api_key, model or None)
        logger.info("Model configured: %s", provider)

    def llm_status(self) -> Dict:
        provider = self.interpreter.provider
        if not provider:
            return {
                "configured": False,
                "provider": self.config.get("provider") or "",
                "model": "",
            }
        name = type(provider).__name__.replace("Provider", "").lower()
        return {
            "configured": True,
            "provider": name,
            "model": getattr(provider, "model", "") or "",
        }

    def score_context(self) -> Optional[Dict]:
        info = self.bridge.score_info
        if not info:
            return None
        return {
            "title": info.title,
            "measures": info.measures,
            "staves": info.staves,
            "time_signature": info.time_signature,
            "key_signature": info.key_signature,
            "parts": info.parts,
        }

    def time_signature(self):
        context = self.score_context() or {}
        signature = context.get("time_signature") or {}
        return (
            int(signature.get("numerator") or 4),
            int(signature.get("denominator") or 4),
        )

    def _generator(self) -> MusicGenerator:
        context = self.score_context() or {}
        fifths = context.get("key_signature")
        key_name = key_signature_name(fifths) if isinstance(fifths, int) else "C"
        return MusicGenerator(key_name, self.time_signature())

    async def handle_request(self, text: str) -> Dict:
        # The plugin is waiting on this HTTP call, so do not also wait for it
        # to poll and answer. The desk watches /status for the confirmation.
        return await self.process_request(text, wait_for_plugin=False)

    async def handle_music(self, action: str, params: Dict) -> Dict:
        return await self.process_music_logic(action, params, wait_for_plugin=False)

    async def process_request(self, user_request: str, wait_for_plugin: Optional[bool] = None) -> Dict:
        context = self.score_context()
        source = "local"
        notes = ""
        intent = ""
        commands: List[dict] = []

        if self.interpreter.provider:
            try:
                response = await self.interpreter.interpret(user_request, context or {})
                source = "llm"
                intent = response.intent
                notes = response.notes or ""
                commands = list(response.commands or [])
                if not commands:
                    local = interpret_locally(user_request, context)
                    if local.commands:
                        commands = local.commands
                        intent = local.intent or intent
                        source = "local"
                        notes = (notes + " The model returned no commands, so the local theory engine wrote them.").strip()
            except Exception as exc:
                logger.exception("Model request failed")
                local = interpret_locally(user_request, context)
                commands = local.commands
                intent = local.intent
                source = "local"
                notes = f"The model did not answer ({exc}). {local.notes}".strip()
        else:
            local = interpret_locally(user_request, context)
            commands = local.commands
            intent = local.intent
            notes = local.notes

        return await self._dispatch(
            commands,
            intent=intent,
            notes=notes,
            source=source,
            wait_for_plugin=wait_for_plugin,
        )

    async def process_music_logic(self, action: str, params: Dict, wait_for_plugin: Optional[bool] = None) -> Dict:
        generator = self._generator()
        track = int(params.get("track") or 0)
        try:
            measures = max(1, min(int(params.get("measures") or 4), 256))
        except (TypeError, ValueError):
            measures = 4

        if action == "walking_bass":
            chords = params.get("chords") or []
            if isinstance(chords, str):
                chords = chords.split()
            chords = [str(chord).strip() for chord in chords if str(chord).strip()]
            if not chords:
                return self._empty_result("Walking bass", "Name the chords, for example G C D G.")
            try:
                commands = generator.walking_bass_line(chords, measures, track=track)
            except ValueError as exc:
                return self._empty_result("Walking bass", str(exc))
            intent = f"Walking bass on {' '.join(chords)} for {measures} bars"
            notes = "One chord tone per beat, walking into the next chord."
        elif action == "drum_pattern":
            style = str(params.get("style") or "rock").lower()
            if style not in ("rock", "jazz", "pop", "latin", "metal"):
                return self._empty_result("Drums", "Style must be rock, jazz, pop, latin, or metal.")
            commands = generator.drum_pattern(style, measures, track=track)
            intent = f"{style.capitalize()} drums for {measures} bars"
            notes = "Hits on the same beat are written together."
            if generator.time_sig != (4, 4):
                notes += " These patterns are written in 4/4."
        else:
            return self._empty_result(action or "Music", f"Unknown action: {action}")

        return await self._dispatch(
            commands,
            intent=intent,
            notes=notes,
            source="local",
            wait_for_plugin=wait_for_plugin,
        )

    def _empty_result(self, intent: str, note: str) -> Dict:
        return {
            "success": False,
            "status": "invalid",
            "intent": intent,
            "notes": note,
            "source": "local",
            "commands_sent": 0,
            "commands": [],
            "preview": [],
            "errors": [note],
            "warnings": [],
            "batch_id": None,
        }

    async def _dispatch(
        self,
        commands: List[dict],
        intent: str,
        notes: str,
        source: str,
        errors: Optional[List[str]] = None,
        wait_for_plugin: Optional[bool] = None,
    ) -> Dict:
        result = {
            "success": False,
            "status": "invalid",
            "intent": intent,
            "notes": notes,
            "source": source,
            "commands_sent": 0,
            "commands": [],
            "preview": [],
            "errors": list(errors or []),
            "warnings": [],
            "batch_id": None,
        }
        if not commands:
            if not result["errors"]:
                result["errors"].append("No commands generated")
            return result

        context = self.score_context()
        if context:
            validator = CommandValidator(context)
        else:
            validator = CommandValidator({"measures": 1000, "staves": 0})
        valid, validation_errors = validator.validate_commands(commands)
        result["errors"].extend(validation_errors)
        result["warnings"].extend(validator.last_warnings)
        if not valid:
            result["errors"].append("No valid commands after validation")
            return result

        valid = order_commands(valid)
        signature = self.time_signature()
        result["commands"] = valid
        result["preview"] = [describe_command(command, signature) for command in valid]

        should_wait = self.bridge.plugin_connected() if wait_for_plugin is None else wait_for_plugin
        delivery = await self.bridge.send_commands(
            [AtomicCommand(command["type"], command) for command in valid],
            wait=should_wait,
        )
        result["commands_sent"] = len(valid)
        result["batch_id"] = delivery.batch_id

        if should_wait and delivery.confirmed and delivery.failed == 0:
            result["success"] = True
            result["status"] = "applied"
        elif should_wait and delivery.confirmed:
            result["success"] = False
            result["status"] = "failed"
            result["errors"].extend(delivery.errors or ["MuseScore reported a problem."])
        elif should_wait:
            result["success"] = False
            result["status"] = "unconfirmed"
            result["errors"].append("The plugin did not confirm. Leave LLM Bridge open and connected in MuseScore.")
        else:
            result["success"] = True
            result["status"] = "queued"
        return result

    async def run_cli(self):
        self._print_banner(interactive=True)
        while True:
            try:
                user_input = (await asyncio.to_thread(input, ">>> ")).strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not user_input:
                continue
            try:
                if user_input == "/quit":
                    print("Goodbye!")
                    break
                if user_input == "/info":
                    self._print_score()
                    continue
                if user_input == "/ping":
                    if self.bridge.plugin_connected():
                        print("Plugin connected")
                    else:
                        print("Plugin not connected. In MuseScore: Plugins → LLM Bridge → Connect.")
                    continue
                if user_input == "/bass":
                    chords = (await asyncio.to_thread(input, "Chords (e.g., G C D G): ")).strip().split()
                    measures_text = (await asyncio.to_thread(input, "Measures: ")).strip() or "4"
                    result = await self.process_music_logic("walking_bass", {
                        "chords": chords,
                        "measures": int(measures_text),
                    })
                    self._print_result(result)
                    continue
                if user_input == "/drums":
                    style = (await asyncio.to_thread(input, "Style (rock/jazz/pop/latin/metal): ")).strip() or "rock"
                    measures_text = (await asyncio.to_thread(input, "Measures: ")).strip() or "4"
                    result = await self.process_music_logic("drum_pattern", {
                        "style": style,
                        "measures": int(measures_text),
                    })
                    self._print_result(result)
                    continue

                result = await self.process_request(user_input)
                self._print_result(result)
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break
            except Exception as exc:
                print(f"Error: {exc}")

    def _print_banner(self, interactive: bool):
        status = self.llm_status()
        if status["configured"]:
            model_line = f"Model:   {status['provider']} · {status['model']}"
        else:
            model_line = "Theory:  local engine (no API key)"
        print("\n" + "=" * 60)
        print("LLM Bridge" + ("  ·  interactive" if interactive else "  ·  headless"))
        print("=" * 60)
        print(f"Desk:    http://localhost:{self.bridge.port}")
        print("Plugin:  Plugins → LLM Bridge → Connect")
        print(model_line)
        if interactive:
            print("\nType a request, or /bass  /drums  /info  /ping  /quit\n")
        else:
            print("\nLeave this running. Press Ctrl+C to stop.\n")

    def _print_score(self):
        info = self.bridge.score_info
        if not info:
            print("No score yet. Connect the plugin with a score open.")
            return
        print(f"Score: {info.title or 'Untitled'}")
        print(f"  Bars: {info.measures}    Staves: {info.staves}")
        print(f"  Time: {info.time_signature}")
        if info.key_signature is not None:
            print(f"  Key:  {key_signature_name(info.key_signature)} ({info.key_signature} fifths)")

    def _print_result(self, result: Dict):
        print(f"\n{result.get('intent') or 'Request'}")
        print(f"Source: {result.get('source')}    Status: {result.get('status')}")
        for line in result.get("preview") or []:
            print(f"  {line}")
        if result.get("notes"):
            print(result["notes"])
        for warning in result.get("warnings") or []:
            print(f"Warning: {warning}")
        for error in result.get("errors") or []:
            print(f"Error: {error}")
        print()


async def main(headless: bool = False, host: str = "localhost", port: int = 8766):
    server = LLMBridgeServer(host=host, port=port)
    if server.config.get("api_key"):
        try:
            server.configure_llm(
                server.config.get("provider", "claude"),
                server.config["api_key"],
                server.config.get("model") or None,
            )
        except Exception as exc:
            logger.error("Could not configure the model (%s). Using the local theory engine.", exc)
    else:
        logger.warning("No API key configured. Common requests use the local theory engine.")

    server_task = asyncio.create_task(server.bridge.start_server())
    for _ in range(50):
        if server.bridge._tcp is not None:
            break
        await asyncio.sleep(0.02)

    try:
        if headless:
            server._print_banner(interactive=False)
            await asyncio.Future()
        else:
            await server.run_cli()
    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    headless = "--headless" in sys.argv or "-H" in sys.argv
    try:
        asyncio.run(main(headless=headless))
    except KeyboardInterrupt:
        print("\nShutting down...")
