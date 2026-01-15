#!/usr/bin/env python3
"""
Command Validator - Validates and sanitizes commands before sending to MuseScore
Prevents invalid commands that would break the score
"""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of command validation"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    sanitized_command: Optional[Dict[str, Any]]


class CommandValidator:
    """Validates atomic commands for MuseScore"""

    # Valid MIDI pitch range
    MIN_PITCH = 0
    MAX_PITCH = 127

    # Valid duration values (in ticks)
    VALID_DURATIONS = [60, 120, 180, 240, 360, 480, 720, 960, 1440, 1920]

    # Maximum reasonable values
    MAX_MEASURE = 1000
    MAX_TRACK = 100
    MAX_BPM = 400
    MIN_BPM = 20

    # Valid dynamic markings
    VALID_DYNAMICS = ["pppp", "ppp", "pp", "p", "mp", "mf", "f", "ff", "fff", "ffff", "fp", "sfz", "sf", "rf", "rfz"]

    def __init__(self, score_context: Dict = None):
        """
        Initialize validator with score context

        Args:
            score_context: Current score information (measures, staves, etc.)
        """
        self.score_context = score_context or {}
        self.max_measures = self.score_context.get("measures", self.MAX_MEASURE)
        self.max_tracks = self.score_context.get("staves", 1) * 4  # 4 voices per staff
        self.time_sig = self.score_context.get("time_signature", {"numerator": 4, "denominator": 4})
        self.ticks_per_measure = 480 * self.time_sig.get("numerator", 4)

    def validate_command(self, command: Dict[str, Any]) -> ValidationResult:
        """Validate a single command"""
        errors = []
        warnings = []

        cmd_type = command.get("type")
        if not cmd_type:
            return ValidationResult(False, ["Missing command type"], [], None)

        # Dispatch to specific validator
        validators = {
            "add_note": self._validate_add_note,
            "add_chord": self._validate_add_chord,
            "add_rest": self._validate_add_rest,
            "add_dynamic": self._validate_add_dynamic,
            "add_tempo": self._validate_add_tempo,
            "add_text": self._validate_add_text,
            "transpose": self._validate_transpose,
            "delete_selection": self._validate_delete,
            "select_range": self._validate_select,
        }

        validator = validators.get(cmd_type)
        if not validator:
            return ValidationResult(False, [f"Unknown command type: {cmd_type}"], [], None)

        return validator(command)

    def validate_commands(self, commands: List[Dict[str, Any]]) -> Tuple[List[Dict], List[str]]:
        """
        Validate a list of commands

        Returns:
            Tuple of (valid_commands, all_errors)
        """
        valid_commands = []
        all_errors = []

        for i, cmd in enumerate(commands):
            result = self.validate_command(cmd)

            if result.valid:
                valid_commands.append(result.sanitized_command or cmd)
                if result.warnings:
                    logger.warning(f"Command {i}: {', '.join(result.warnings)}")
            else:
                all_errors.extend([f"Command {i} ({cmd.get('type', '?')}): {e}" for e in result.errors])
                logger.error(f"Invalid command {i}: {result.errors}")

        return valid_commands, all_errors

    def _validate_add_note(self, cmd: Dict) -> ValidationResult:
        """Validate add_note command"""
        errors = []
        warnings = []
        sanitized = dict(cmd)

        # Validate pitch
        pitch = cmd.get("pitch")
        if pitch is None:
            errors.append("Missing pitch")
        elif not isinstance(pitch, int):
            errors.append(f"Pitch must be integer, got {type(pitch)}")
        elif pitch < self.MIN_PITCH or pitch > self.MAX_PITCH:
            errors.append(f"Pitch {pitch} out of range ({self.MIN_PITCH}-{self.MAX_PITCH})")

        # Validate duration
        duration = cmd.get("duration", 480)
        if duration not in self.VALID_DURATIONS:
            # Find nearest valid duration
            nearest = min(self.VALID_DURATIONS, key=lambda x: abs(x - duration))
            warnings.append(f"Duration {duration} adjusted to {nearest}")
            sanitized["duration"] = nearest

        # Validate measure
        measure = cmd.get("measure", 0)
        if measure < 0:
            errors.append(f"Measure cannot be negative: {measure}")
        elif measure >= self.max_measures:
            warnings.append(f"Measure {measure} may exceed score length ({self.max_measures})")

        # Validate track
        track = cmd.get("track", 0)
        if track < 0 or track >= self.max_tracks:
            errors.append(f"Track {track} out of range (0-{self.max_tracks - 1})")

        return ValidationResult(len(errors) == 0, errors, warnings, sanitized)

    def _validate_add_chord(self, cmd: Dict) -> ValidationResult:
        """Validate add_chord command"""
        errors = []
        warnings = []
        sanitized = dict(cmd)

        # Validate pitches array
        pitches = cmd.get("pitches")
        if not pitches:
            errors.append("Missing pitches array")
        elif not isinstance(pitches, list):
            errors.append("Pitches must be an array")
        elif len(pitches) == 0:
            errors.append("Pitches array is empty")
        elif len(pitches) > 12:
            warnings.append(f"Chord has {len(pitches)} notes, limiting to 12")
            sanitized["pitches"] = pitches[:12]
        else:
            # Validate each pitch
            for i, p in enumerate(pitches):
                if not isinstance(p, int) or p < self.MIN_PITCH or p > self.MAX_PITCH:
                    errors.append(f"Invalid pitch at index {i}: {p}")

        # Validate duration
        duration = cmd.get("duration", 480)
        if duration not in self.VALID_DURATIONS:
            nearest = min(self.VALID_DURATIONS, key=lambda x: abs(x - duration))
            warnings.append(f"Duration {duration} adjusted to {nearest}")
            sanitized["duration"] = nearest

        # Validate measure and track
        measure = cmd.get("measure", 0)
        if measure < 0:
            errors.append(f"Measure cannot be negative")

        track = cmd.get("track", 0)
        if track < 0 or track >= self.max_tracks:
            errors.append(f"Track {track} out of range")

        return ValidationResult(len(errors) == 0, errors, warnings, sanitized)

    def _validate_add_rest(self, cmd: Dict) -> ValidationResult:
        """Validate add_rest command"""
        errors = []
        warnings = []
        sanitized = dict(cmd)

        duration = cmd.get("duration", 480)
        if duration not in self.VALID_DURATIONS:
            nearest = min(self.VALID_DURATIONS, key=lambda x: abs(x - duration))
            sanitized["duration"] = nearest

        measure = cmd.get("measure", 0)
        if measure < 0:
            errors.append("Measure cannot be negative")

        return ValidationResult(len(errors) == 0, errors, warnings, sanitized)

    def _validate_add_dynamic(self, cmd: Dict) -> ValidationResult:
        """Validate add_dynamic command"""
        errors = []
        warnings = []
        sanitized = dict(cmd)

        dynamic = cmd.get("dynamic", "mf")
        if dynamic.lower() not in self.VALID_DYNAMICS:
            warnings.append(f"Unknown dynamic '{dynamic}', using 'mf'")
            sanitized["dynamic"] = "mf"

        measure = cmd.get("measure", 0)
        if measure < 0:
            errors.append("Measure cannot be negative")

        return ValidationResult(len(errors) == 0, errors, warnings, sanitized)

    def _validate_add_tempo(self, cmd: Dict) -> ValidationResult:
        """Validate add_tempo command"""
        errors = []
        warnings = []
        sanitized = dict(cmd)

        bpm = cmd.get("bpm", 120)
        if not isinstance(bpm, (int, float)):
            errors.append(f"BPM must be a number, got {type(bpm)}")
        elif bpm < self.MIN_BPM:
            warnings.append(f"BPM {bpm} too slow, setting to {self.MIN_BPM}")
            sanitized["bpm"] = self.MIN_BPM
        elif bpm > self.MAX_BPM:
            warnings.append(f"BPM {bpm} too fast, setting to {self.MAX_BPM}")
            sanitized["bpm"] = self.MAX_BPM

        return ValidationResult(len(errors) == 0, errors, warnings, sanitized)

    def _validate_add_text(self, cmd: Dict) -> ValidationResult:
        """Validate add_text command"""
        errors = []
        warnings = []
        sanitized = dict(cmd)

        text = cmd.get("text", "")
        if not text:
            warnings.append("Empty text")

        text_type = cmd.get("textType", "staff")
        if text_type not in ["staff", "system", "lyrics"]:
            warnings.append(f"Unknown textType '{text_type}', using 'staff'")
            sanitized["textType"] = "staff"

        return ValidationResult(len(errors) == 0, errors, warnings, sanitized)

    def _validate_transpose(self, cmd: Dict) -> ValidationResult:
        """Validate transpose command"""
        errors = []
        warnings = []
        sanitized = dict(cmd)

        semitones = cmd.get("semitones", 0)
        if not isinstance(semitones, int):
            errors.append(f"Semitones must be integer")
        elif abs(semitones) > 24:
            warnings.append(f"Large transposition ({semitones} semitones)")

        return ValidationResult(len(errors) == 0, errors, warnings, sanitized)

    def _validate_delete(self, cmd: Dict) -> ValidationResult:
        """Validate delete command"""
        return ValidationResult(True, [], [], cmd)

    def _validate_select(self, cmd: Dict) -> ValidationResult:
        """Validate select command"""
        errors = []
        warnings = []

        start = cmd.get("startMeasure", 0)
        end = cmd.get("endMeasure", start)

        if start < 0 or end < 0:
            errors.append("Measure cannot be negative")
        if end < start:
            errors.append("End measure must be >= start measure")

        return ValidationResult(len(errors) == 0, errors, warnings, cmd)


def validate_beats_in_measure(commands: List[Dict], time_sig: Tuple[int, int] = (4, 4)) -> List[str]:
    """
    Check if commands would result in invalid measure content

    Args:
        commands: List of note/rest commands
        time_sig: Time signature as (numerator, denominator)

    Returns:
        List of warning messages
    """
    warnings = []
    ticks_per_measure = 480 * time_sig[0]  # Assuming 480 ticks per quarter

    # Group commands by measure
    measures = {}
    for cmd in commands:
        if cmd.get("type") in ["add_note", "add_chord", "add_rest"]:
            measure = cmd.get("measure", 0)
            duration = cmd.get("duration", 480)
            if measure not in measures:
                measures[measure] = 0
            measures[measure] += duration

    # Check each measure
    for measure, total_ticks in measures.items():
        if total_ticks > ticks_per_measure:
            warnings.append(
                f"Measure {measure} has {total_ticks} ticks but should have {ticks_per_measure} "
                f"({time_sig[0]}/{time_sig[1]} time signature)"
            )

    return warnings


# Test
if __name__ == "__main__":
    validator = CommandValidator({
        "measures": 16,
        "staves": 2,
        "time_signature": {"numerator": 4, "denominator": 4}
    })

    test_commands = [
        {"type": "add_note", "pitch": 60, "duration": 480, "measure": 0},
        {"type": "add_note", "pitch": 200, "duration": 480, "measure": 0},  # Invalid pitch
        {"type": "add_chord", "pitches": [60, 64, 67], "duration": 500, "measure": 1},  # Invalid duration
        {"type": "add_dynamic", "dynamic": "xyz", "measure": 2},  # Invalid dynamic
        {"type": "add_tempo", "bpm": 500, "measure": 0},  # BPM too high
    ]

    print("Validating commands:")
    for i, cmd in enumerate(test_commands):
        result = validator.validate_command(cmd)
        status = "✓" if result.valid else "✗"
        print(f"  {status} Command {i}: {cmd.get('type')}")
        if result.errors:
            print(f"    Errors: {result.errors}")
        if result.warnings:
            print(f"    Warnings: {result.warnings}")
