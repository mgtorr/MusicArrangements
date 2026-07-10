#!/usr/bin/env python3
"""
LLM Interpreter - Translates natural language to music commands
Uses Claude, Gemini, or OpenAI to interpret user requests
Enhanced with composition assistant capabilities
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

import httpx

from composition_prompts import (
    MUSIC_THEORY_CONTEXT,
    get_task_prompt,
    get_style_prompt,
    ARRANGEMENT_PROMPT
)

logger = logging.getLogger(__name__)


# === COMMAND SCHEMA ===
COMMAND_SCHEMA = """
You are a MuseScore Composition Assistant and Automator. Convert user requests into atomic commands.

AVAILABLE COMMANDS:
1. add_note: Add a single note
   {"type": "add_note", "pitch": <MIDI 0-127>, "duration": <ticks>, "measure": <int>, "track": <int>}
   Duration: 1920=whole, 960=half, 480=quarter, 240=eighth, 120=16th

2. add_chord: Add a chord (multiple notes)
   {"type": "add_chord", "pitches": [<MIDI>, ...], "duration": <ticks>, "measure": <int>, "track": <int>}

3. add_rest: Add a rest
   {"type": "add_rest", "duration": <ticks>, "measure": <int>, "track": <int>}

4. add_dynamic: Add dynamic marking
   {"type": "add_dynamic", "dynamic": "pp|p|mp|mf|f|ff|sfz", "measure": <int>, "track": <int>}

5. add_tempo: Add tempo marking
   {"type": "add_tempo", "bpm": <int>, "measure": <int>, "text": "<optional>"}

6. add_text: Add text annotation
   {"type": "add_text", "text": "<string>", "measure": <int>, "track": <int>, "textType": "staff|system|lyrics"}

7. transpose: Transpose selection
   {"type": "transpose", "semitones": <int>}

MIDI PITCH REFERENCE:
C4 (middle C) = 60, D4 = 62, E4 = 64, F4 = 65, G4 = 67, A4 = 69, B4 = 71
Add 12 for each octave up, subtract 12 for each octave down.
C3 = 48, C5 = 72, C2 = 36 (bass), etc.

MUSIC THEORY CONTEXT:
{music_theory_context}

OUTPUT FORMAT:
Respond with ONLY a JSON object:
{{
  "intent": "<brief description of what user wants>",
  "commands": [<array of command objects>],
  "notes": "<any important notes or music theory explanations>"
}}
"""


@dataclass
class LLMResponse:
    """Parsed LLM response"""
    intent: str
    commands: List[Dict[str, Any]]
    notes: str
    raw: str


class LLMProvider(ABC):
    """Abstract base for LLM providers"""

    @abstractmethod
    async def interpret(self, user_request: str, score_context: Dict) -> LLMResponse:
        pass


class ClaudeProvider(LLMProvider):
    """Anthropic Claude provider"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://api.anthropic.com/v1/messages"

    async def interpret(self, user_request: str, score_context: Dict) -> LLMResponse:
        prompt = self._build_prompt(user_request, score_context)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.endpoint,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": self.model,
                    "max_tokens": 8192,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=60.0
            )

            if response.status_code != 200:
                raise Exception(f"Claude API error: {response.status_code} - {response.text}")

            data = response.json()
            content = data["content"][0]["text"]
            return self._parse_response(content)

    def _build_prompt(self, user_request: str, score_context: Dict) -> str:
        context_str = json.dumps(score_context, indent=2) if score_context else "No score open"
        
        # Detect if this is a specialized composition request
        request_lower = user_request.lower()
        
        # Check for task-specific keywords
        if any(keyword in request_lower for keyword in ["melody", "melodic", "tune", "theme"]):
            base_prompt = get_task_prompt("melody")
        elif any(keyword in request_lower for keyword in ["harmonize", "harmony", "chord progression", "chords"]):
            base_prompt = get_task_prompt("harmony")
        elif any(keyword in request_lower for keyword in ["rhythm", "groove", "beat"]):
            base_prompt = get_task_prompt("rhythm")
        elif any(keyword in request_lower for keyword in ["bass", "bassline", "bass line"]):
            base_prompt = get_task_prompt("bass")
        elif any(keyword in request_lower for keyword in ["form", "structure", "sections"]):
            base_prompt = get_task_prompt("form")
        # Check for style-specific keywords
        elif any(style in request_lower for style in ["jazz", "classical", "pop", "rock", "blues", "folk"]):
            for style in ["jazz", "classical", "pop", "rock", "blues", "folk"]:
                if style in request_lower:
                    base_prompt = get_style_prompt(style)
                    break
            else:
                base_prompt = ARRANGEMENT_PROMPT
        else:
            base_prompt = ARRANGEMENT_PROMPT
        
        # Format with context
        schema_formatted = COMMAND_SCHEMA.format(music_theory_context=MUSIC_THEORY_CONTEXT)
        
        return f"""{schema_formatted}

{base_prompt.format(
    music_theory_context=MUSIC_THEORY_CONTEXT,
    score_context=context_str,
    user_request=user_request
)}

Generate the commands to fulfill this request. Output ONLY valid JSON."""

    def _parse_response(self, content: str) -> LLMResponse:
        # Find JSON in response
        start = content.find("{")
        end = content.rfind("}") + 1

        if start == -1 or end <= start:
            return LLMResponse(
                intent="Could not parse",
                commands=[],
                notes=content,
                raw=content
            )

        try:
            data = json.loads(content[start:end])
            return LLMResponse(
                intent=data.get("intent", ""),
                commands=data.get("commands", []),
                notes=data.get("notes", ""),
                raw=content
            )
        except json.JSONDecodeError as e:
            return LLMResponse(
                intent="JSON parse error",
                commands=[],
                notes=str(e),
                raw=content
            )


class GeminiProvider(LLMProvider):
    """Google Gemini provider"""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model

    async def interpret(self, user_request: str, score_context: Dict) -> LLMResponse:
        prompt = self._build_prompt(user_request, score_context)
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 8192
                    }
                },
                timeout=60.0
            )

            if response.status_code != 200:
                raise Exception(f"Gemini API error: {response.status_code} - {response.text}")

            data = response.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            return self._parse_response(content)

    def _build_prompt(self, user_request: str, score_context: Dict) -> str:
        context_str = json.dumps(score_context, indent=2) if score_context else "No score open"
        
        # Detect specialized composition request (same as Claude)
        request_lower = user_request.lower()
        
        if any(keyword in request_lower for keyword in ["melody", "melodic", "tune", "theme"]):
            base_prompt = get_task_prompt("melody")
        elif any(keyword in request_lower for keyword in ["harmonize", "harmony", "chord progression", "chords"]):
            base_prompt = get_task_prompt("harmony")
        elif any(keyword in request_lower for keyword in ["rhythm", "groove", "beat"]):
            base_prompt = get_task_prompt("rhythm")
        elif any(keyword in request_lower for keyword in ["bass", "bassline", "bass line"]):
            base_prompt = get_task_prompt("bass")
        elif any(keyword in request_lower for keyword in ["form", "structure", "sections"]):
            base_prompt = get_task_prompt("form")
        elif any(style in request_lower for style in ["jazz", "classical", "pop", "rock", "blues", "folk"]):
            for style in ["jazz", "classical", "pop", "rock", "blues", "folk"]:
                if style in request_lower:
                    base_prompt = get_style_prompt(style)
                    break
            else:
                base_prompt = ARRANGEMENT_PROMPT
        else:
            base_prompt = ARRANGEMENT_PROMPT
        
        schema_formatted = COMMAND_SCHEMA.format(music_theory_context=MUSIC_THEORY_CONTEXT)
        
        return f"""{schema_formatted}

{base_prompt.format(
    music_theory_context=MUSIC_THEORY_CONTEXT,
    score_context=context_str,
    user_request=user_request
)}

Generate the commands to fulfill this request. Output ONLY valid JSON."""

    def _parse_response(self, content: str) -> LLMResponse:
        start = content.find("{")
        end = content.rfind("}") + 1

        if start == -1 or end <= start:
            return LLMResponse(intent="Could not parse", commands=[], notes=content, raw=content)

        try:
            data = json.loads(content[start:end])
            return LLMResponse(
                intent=data.get("intent", ""),
                commands=data.get("commands", []),
                notes=data.get("notes", ""),
                raw=content
            )
        except json.JSONDecodeError as e:
            return LLMResponse(intent="JSON parse error", commands=[], notes=str(e), raw=content)


class OpenAIProvider(LLMProvider):
    """OpenAI provider"""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://api.openai.com/v1/chat/completions"

    async def interpret(self, user_request: str, score_context: Dict) -> LLMResponse:
        prompt = self._build_prompt(user_request, score_context)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.endpoint,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a MuseScore composition assistant. Output only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 8192
                },
                timeout=60.0
            )

            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return self._parse_response(content)

    def _build_prompt(self, user_request: str, score_context: Dict) -> str:
        context_str = json.dumps(score_context, indent=2) if score_context else "No score open"
        
        # Detect specialized composition request (same as others)
        request_lower = user_request.lower()
        
        if any(keyword in request_lower for keyword in ["melody", "melodic", "tune", "theme"]):
            base_prompt = get_task_prompt("melody")
        elif any(keyword in request_lower for keyword in ["harmonize", "harmony", "chord progression", "chords"]):
            base_prompt = get_task_prompt("harmony")
        elif any(keyword in request_lower for keyword in ["rhythm", "groove", "beat"]):
            base_prompt = get_task_prompt("rhythm")
        elif any(keyword in request_lower for keyword in ["bass", "bassline", "bass line"]):
            base_prompt = get_task_prompt("bass")
        elif any(keyword in request_lower for keyword in ["form", "structure", "sections"]):
            base_prompt = get_task_prompt("form")
        elif any(style in request_lower for style in ["jazz", "classical", "pop", "rock", "blues", "folk"]):
            for style in ["jazz", "classical", "pop", "rock", "blues", "folk"]:
                if style in request_lower:
                    base_prompt = get_style_prompt(style)
                    break
            else:
                base_prompt = ARRANGEMENT_PROMPT
        else:
            base_prompt = ARRANGEMENT_PROMPT
        
        schema_formatted = COMMAND_SCHEMA.format(music_theory_context=MUSIC_THEORY_CONTEXT)
        
        return f"""{schema_formatted}

{base_prompt.format(
    music_theory_context=MUSIC_THEORY_CONTEXT,
    score_context=context_str,
    user_request=user_request
)}

Generate the commands to fulfill this request."""

    def _parse_response(self, content: str) -> LLMResponse:
        start = content.find("{")
        end = content.rfind("}") + 1

        if start == -1 or end <= start:
            return LLMResponse(intent="Could not parse", commands=[], notes=content, raw=content)

        try:
            data = json.loads(content[start:end])
            return LLMResponse(
                intent=data.get("intent", ""),
                commands=data.get("commands", []),
                notes=data.get("notes", ""),
                raw=content
            )
        except json.JSONDecodeError as e:
            return LLMResponse(intent="JSON parse error", commands=[], notes=str(e), raw=content)


class LLMInterpreter:
    """Main interpreter class that manages LLM providers"""

    def __init__(self):
        self.provider: Optional[LLMProvider] = None

    def set_provider(self, provider_name: str, api_key: str, model: Optional[str] = None):
        """Set the LLM provider"""
        if provider_name.lower() == "claude":
            self.provider = ClaudeProvider(api_key, model or "claude-sonnet-4-20250514")
        elif provider_name.lower() == "gemini":
            self.provider = GeminiProvider(api_key, model or "gemini-2.0-flash")
        elif provider_name.lower() == "openai":
            self.provider = OpenAIProvider(api_key, model or "gpt-4o")
        else:
            raise ValueError(f"Unknown provider: {provider_name}")

        logger.info(f"LLM provider set to {provider_name}")

    async def interpret(self, user_request: str, score_context: Dict = None) -> LLMResponse:
        """Interpret a user request"""
        if not self.provider:
            raise Exception("No LLM provider configured")

        logger.info(f"Interpreting: {user_request}")
        response = await self.provider.interpret(user_request, score_context or {})
        logger.info(f"Intent: {response.intent}, Commands: {len(response.commands)}")

        return response


# Singleton
interpreter = LLMInterpreter()


# Test
if __name__ == "__main__":
    import asyncio

    async def test():
        # You would need to set your API key
        api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Set ANTHROPIC_API_KEY or GEMINI_API_KEY environment variable")
            return

        interpreter.set_provider("claude", api_key)

        score_context = {
            "title": "Test Score",
            "measures": 8,
            "staves": 1,
            "time_signature": {"numerator": 4, "denominator": 4},
            "key_signature": 0
        }

        response = await interpreter.interpret(
            "Add a C major chord at the beginning",
            score_context
        )

        print(f"Intent: {response.intent}")
        print(f"Commands: {json.dumps(response.commands, indent=2)}")
        print(f"Notes: {response.notes}")

    asyncio.run(test())
