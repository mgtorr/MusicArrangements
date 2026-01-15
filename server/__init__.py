"""
LLM Bridge Server
Middleware between MuseScore and LLM for AI-powered music arrangement
"""

from .bridge_server import MuseScoreBridge, AtomicCommand
from .llm_interpreter import LLMInterpreter, interpreter
from .music_logic import MusicGenerator
from .validator import CommandValidator

__version__ = "2.0.0"
__all__ = [
    "MuseScoreBridge",
    "AtomicCommand",
    "LLMInterpreter",
    "interpreter",
    "MusicGenerator",
    "CommandValidator",
]
