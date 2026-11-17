#!/usr/bin/env python3
"""
Command validator.

Checks atomic commands before they reach MuseScore and snaps durations
onto the tick values the plugin can spell.
"""

from typing import Any, Dict, List, Optional, Tuple
import logging

from durations import FRACTION_BY_TICKS, measure_length, nearest_duration

logger = logging.getLogger(__name__)

RHYTHMIC = {"add_note", "add_chord", "add_rest"}


class ValidationResult:
    def __init__(self, valid: bool, errors: List[str], warnings: List[str], sanitized_command: Optional[Dict[str, Any]]):
        self.valid = valid
        self.errors = errors
        self.warnings = warnings
        self.sanitized_command = sanitized_command


class CommandValidator:
    """Validates atomic commands for MuseScore."""

    MIN_PITCH = 0
    MAX_PITCH = 127
    VALID_DURATIONS = sorted(FRACTION_BY_TICKS)
    MAX_MEASURE = 1000
    MAX_TRACK = 100
    MAX_BPM = 400
    MIN_BPM = 20
    VALID_DYNAMICS = [
        "pppp", "ppp", "pp", "p", "mp", "mf", "f", "ff", "fff", "ffff",
        "fp", "sfz", "sf", "rf", "rfz",
    ]

    def __init__(self, score_context: Dict = None):
        self.score_context = score_context or {}
        self.max_measures = self.score_context.get("measures", self.MAX_MEASURE)
        staves = self.score_context.get("staves") or 1
        self.max_tracks = max(staves * 4, 1)
        self.time_sig = self.score_context.get("time_signature") or {"numerator": 4, "denominator": 4}
        self.ticks_per_measure = measure_length(
            int(self.time_sig.get("numerator") or 4),
            int(self.time_sig.get("denominator") or 4),
        )
        self.last_warnings: List[str] = []

    def validate_command(self, command: Dict[str, Any]) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        cmd_type = command.get("type")
        if not cmd_type:
            return ValidationResult(False, ["Missing command type"], [], None)

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
        valid_commands = []
        all_errors = []
        warnings: List[str] = []

        for index, command in enumerate(commands):
            result = self.validate_command(command)
            if result.warnings:
                warnings.extend(f"Command {index}: {warning}" for warning in result.warnings)
            if result.valid:
                valid_commands.append(result.sanitized_command or command)
            else:
                all_errors.extend(
                    f"Command {index} ({command.get('type', '?')}): {error}" for error in result.errors
                )
                logger.error("Invalid command %s: %s", index, result.errors)

        warnings.extend(self._beat_warnings(valid_commands))
        self.last_warnings = warnings
        for warning in warnings:
            logger.warning(warning)
        return valid_commands, all_errors

    def _beat_warnings(self, commands: List[Dict[str, Any]]) -> List[str]:
        warnings = []
        by_measure: Dict[int, List[dict]] = {}
        for command in commands:
            if command.get("type") not in RHYTHMIC:
                continue
            by_measure.setdefault(int(command.get("measure") or 0), []).append(command)

        for measure, group in sorted(by_measure.items()):
            if any(command.get("tick") is None for command in group):
                total = sum(int(command.get("duration") or 0) for command in group)
                if total > self.ticks_per_measure:
                    warnings.append(
                        f"Bar {measure + 1} holds {total} ticks of music "
                        f"and the time signature holds {self.ticks_per_measure}"
                    )
                continue

            end = 0
            for command in group:
                tick = int(command.get("tick") or 0)
                duration = int(command.get("duration") or 0)
                end = max(end, tick + duration)
            if end > self.ticks_per_measure:
                warnings.append(
                    f"Bar {measure + 1} is written out to tick {end}, "
                    f"past the bar length of {self.ticks_per_measure}"
                )
        return warnings

    def _validate_add_note(self, command: Dict) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        sanitized = dict(command)

        pitch = self._as_int(command.get("pitch"), "Pitch", errors)
        if pitch is not None:
            sanitized["pitch"] = pitch
            if pitch < self.MIN_PITCH or pitch > self.MAX_PITCH:
                errors.append(f"Pitch {pitch} out of range ({self.MIN_PITCH}-{self.MAX_PITCH})")

        self._apply_duration(command, sanitized, warnings)
        self._apply_measure(command, sanitized, errors, warnings)
        self._apply_track(command, sanitized, errors)
        self._apply_tick(command, sanitized, errors, warnings)
        return ValidationResult(len(errors) == 0, errors, warnings, sanitized)

    def _validate_add_chord(self, command: Dict) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        sanitized = dict(command)

        pitches = command.get("pitches")
        if not isinstance(pitches, list) or len(pitches) == 0:
            errors.append("Chord needs a list of pitches")
        else:
            cleaned = []
            for index, value in enumerate(pitches):
                pitch = self._as_int(value, f"Pitch {index}", errors)
                if pitch is None:
                    continue
                if pitch < self.MIN_PITCH or pitch > self.MAX_PITCH:
                    errors.append(f"Invalid pitch at index {index}: {pitch}")
                else:
                    cleaned.append(pitch)
            if len(cleaned) > 12:
                warnings.append(f"Chord has {len(cleaned)} notes, limiting to 12")
                cleaned = cleaned[:12]
            sanitized["pitches"] = cleaned
            if not cleaned and not errors:
                errors.append("Pitches array is empty")

        self._apply_duration(command, sanitized, warnings)
        self._apply_measure(command, sanitized, errors, warnings)
        self._apply_track(command, sanitized, errors)
        self._apply_tick(command, sanitized, errors, warnings)
        return ValidationResult(len(errors) == 0, errors, warnings, sanitized)

    def _validate_add_rest(self, command: Dict) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        sanitized = dict(command)
        self._apply_duration(command, sanitized, warnings)
        self._apply_measure(command, sanitized, errors, warnings)
        self._apply_track(command, sanitized, errors)
        self._apply_tick(command, sanitized, errors, warnings)
        return ValidationResult(len(errors) == 0, errors, warnings, sanitized)

    def _validate_add_dynamic(self, command: Dict) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        sanitized = dict(command)
        dynamic = str(command.get("dynamic", "mf")).strip().lower()
        if dynamic not in self.VALID_DYNAMICS:
            warnings.append(f"Unknown dynamic '{command.get('dynamic')}', using 'mf'")
            dynamic = "mf"
        sanitized["dynamic"] = dynamic
        self._apply_measure(command, sanitized, errors, warnings)
        self._apply_track(command, sanitized, errors)
        return ValidationResult(len(errors) == 0, errors, warnings, sanitized)

    def _validate_add_tempo(self, command: Dict) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        sanitized = dict(command)
        bpm = self._as_int(command.get("bpm", 120), "BPM", errors)
        if bpm is not None:
            if bpm < self.MIN_BPM:
                warnings.append(f"BPM {bpm} is very slow, setting to {self.MIN_BPM}")
                bpm = self.MIN_BPM
            elif bpm > self.MAX_BPM:
                warnings.append(f"BPM {bpm} is very fast, setting to {self.MAX_BPM}")
                bpm = self.MAX_BPM
            sanitized["bpm"] = bpm
        self._apply_measure(command, sanitized, errors, warnings)
        return ValidationResult(len(errors) == 0, errors, warnings, sanitized)

    def _validate_add_text(self, command: Dict) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        sanitized = dict(command)
        if not command.get("text"):
            warnings.append("Empty text")
        text_type = command.get("textType", "staff")
        if text_type not in ("staff", "system", "lyrics"):
            warnings.append(f"Unknown textType '{text_type}', using 'staff'")
            sanitized["textType"] = "staff"
        self._apply_measure(command, sanitized, errors, warnings)
        return ValidationResult(len(errors) == 0, errors, warnings, sanitized)

    def _validate_transpose(self, command: Dict) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        sanitized = dict(command)
        semitones = self._as_int(command.get("semitones", 0), "Semitones", errors)
        if semitones is not None:
            sanitized["semitones"] = semitones
            if abs(semitones) > 48:
                errors.append(f"Transposition of {semitones} semitones is too large")
            elif abs(semitones) > 24:
                warnings.append(f"Large transposition ({semitones} semitones)")
        return ValidationResult(len(errors) == 0, errors, warnings, sanitized)

    def _validate_delete(self, command: Dict) -> ValidationResult:
        return ValidationResult(True, [], [], dict(command))

    def _validate_select(self, command: Dict) -> ValidationResult:
        errors: List[str] = []
        start = command.get("startMeasure", 0)
        end = command.get("endMeasure", start)
        if not isinstance(start, int) or not isinstance(end, int) or isinstance(start, bool) or isinstance(end, bool):
            errors.append("Select range needs integer measures")
        else:
            if start < 0 or end < 0:
                errors.append("Measure cannot be negative")
            if end < start:
                errors.append("End measure must be >= start measure")
        return ValidationResult(len(errors) == 0, errors, warnings=[], sanitized_command=dict(command))

    def _apply_duration(self, command: Dict, sanitized: Dict, warnings: List[str]) -> None:
        raw = command.get("duration", 480)
        duration = raw if isinstance(raw, int) and not isinstance(raw, bool) else None
        if duration is None:
            duration = self._as_int(raw, "Duration", [])
        if duration is None:
            duration = 480
        if duration not in FRACTION_BY_TICKS:
            nearest = nearest_duration(duration)
            warnings.append(f"Duration {duration} adjusted to {nearest}")
            duration = nearest
        sanitized["duration"] = duration

    def _apply_measure(self, command: Dict, sanitized: Dict, errors: List[str], warnings: List[str]) -> None:
        measure = self._as_int(command.get("measure", 0), "Measure", errors)
        if measure is None:
            return
        sanitized["measure"] = measure
        if measure < 0:
            errors.append(f"Measure cannot be negative: {measure}")
        elif self.max_measures and measure >= self.max_measures:
            warnings.append(f"Bar {measure + 1} may be past the end of the score ({self.max_measures} bars)")

    def _apply_track(self, command: Dict, sanitized: Dict, errors: List[str]) -> None:
        track = self._as_int(command.get("track", 0), "Track", errors)
        if track is None:
            return
        sanitized["track"] = track
        limit = self.max_tracks if self.score_context.get("staves") else self.MAX_TRACK
        if track < 0 or track >= limit:
            errors.append(f"Track {track} out of range (0-{limit - 1})")

    def _apply_tick(self, command: Dict, sanitized: Dict, errors: List[str], warnings: List[str]) -> None:
        if "tick" not in command or command.get("tick") is None:
            return
        tick = self._as_int(command.get("tick"), "Tick", errors)
        if tick is None:
            return
        sanitized["tick"] = tick
        if tick < 0:
            errors.append("Tick cannot be negative")
        elif tick >= self.ticks_per_measure:
            warnings.append(f"Tick {tick} is past the end of a {self.ticks_per_measure}-tick bar")

    def _as_int(self, value: Any, label: str, errors: List[str]) -> Optional[int]:
        if value is None or isinstance(value, bool):
            errors.append(f"{label} is missing")
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.lstrip("-").isdigit():
                return int(stripped)
        errors.append(f"{label} must be an integer, got {value!r}")
        return None


def order_commands(commands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Put notes, chords, and rests in track / bar / beat order."""
    rhythmic_indexes = [index for index, command in enumerate(commands) if command.get("type") in RHYTHMIC]
    rhythmic = [commands[index] for index in rhythmic_indexes]
    rhythmic.sort(key=lambda command: (
        int(command.get("track") or 0),
        int(command.get("measure") or 0),
        int(command.get("tick") or 0),
    ))
    ordered = list(commands)
    for index, command in zip(rhythmic_indexes, rhythmic):
        ordered[index] = command
    return ordered


def validate_beats_in_measure(commands: List[Dict], time_sig: Tuple[int, int] = (4, 4)) -> List[str]:
    """Backward-compatible wrapper used by older callers."""
    context = {"time_signature": {"numerator": time_sig[0], "denominator": time_sig[1]}, "measures": 1000, "staves": 8}
    validator = CommandValidator(context)
    return validator._beat_warnings(commands)


if __name__ == "__main__":
    validator = CommandValidator({
        "measures": 16,
        "staves": 2,
        "time_signature": {"numerator": 4, "denominator": 4},
    })
    samples = [
        {"type": "add_note", "pitch": 60, "duration": 480, "measure": 0, "tick": 0},
        {"type": "add_note", "pitch": 200, "duration": 480, "measure": 0},
        {"type": "add_chord", "pitches": [60, 64, 67], "duration": 500, "measure": 1},
        {"type": "add_dynamic", "dynamic": "FF", "measure": 2},
        {"type": "add_tempo", "bpm": 500, "measure": 0},
    ]
    for index, command in enumerate(samples):
        result = validator.validate_command(command)
        print(("ok" if result.valid else "bad"), index, command.get("type"), result.errors, result.warnings)
