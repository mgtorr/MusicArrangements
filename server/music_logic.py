#!/usr/bin/env python3
"""
Music logic.

Turns chord symbols, bass lines, and drum patterns into atomic commands
the MuseScore plugin can play in time. Note placement uses `tick`
(0 = downbeat of the bar). A quarter note is 480 ticks.
"""

import re
from typing import Dict, List, Tuple

try:
    from music21 import note, pitch, scale, stream

    MUSIC21_AVAILABLE = True
except ImportError:
    MUSIC21_AVAILABLE = False

from durations import measure_length, ticks_per_beat


class Duration:
    WHOLE = 1920
    HALF = 960
    QUARTER = 480
    EIGHTH = 240
    SIXTEENTH = 120
    THIRTYSECOND = 60
    DOTTED_HALF = 1440
    DOTTED_QUARTER = 720
    DOTTED_EIGHTH = 360


MIDDLE_C = 60

# General MIDI kit names used when a command is marked as drums.
GM_DRUMS = {
    36: "kick",
    38: "snare",
    42: "closed hat",
    46: "open hat",
    49: "crash",
    51: "ride",
}

KEY_FIFTHS = {
    -7: "Cb",
    -6: "Gb",
    -5: "Db",
    -4: "Ab",
    -3: "Eb",
    -2: "Bb",
    -1: "F",
    0: "C",
    1: "G",
    2: "D",
    3: "A",
    4: "E",
    5: "B",
    6: "F#",
    7: "C#",
}

_ACCIDENTALS = {"#": "#", "♯": "#", "b": "b", "♭": "b"}

# Longer suffixes first so "maj7" is not read as minor ("m...") and
# "Gmaj" is not read as minor because the letters contain "m".
_QUALITIES = [
    ("major7", "maj7"),
    ("maj7", "maj7"),
    ("ma7", "maj7"),
    ("minor7", "min7"),
    ("min7", "min7"),
    ("m7", "min7"),
    ("dim7", "dim7"),
    ("dominant7", "dom7"),
    ("dom7", "dom7"),
    ("sus2", "sus2"),
    ("sus4", "sus4"),
    ("add9", "add9"),
    ("power", "power"),
    ("major", "major"),
    ("minor", "minor"),
    ("maj", "major"),
    ("min", "minor"),
    ("dim", "dim"),
    ("aug", "aug"),
    ("m", "minor"),
    ("7", "dom7"),
]

_CHORD_INTERVALS = {
    "major": [0, 4, 7],
    "minor": [0, 3, 7],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "maj7": [0, 4, 7, 11],
    "min7": [0, 3, 7, 10],
    "dom7": [0, 4, 7, 10],
    "dim7": [0, 3, 6, 9],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
    "add9": [0, 4, 7, 14],
    "power": [0, 7],
}

KICK = 36
SNARE = 38
HIHAT_CLOSED = 42
HIHAT_OPEN = 46
RIDE = 51
CRASH = 49

# Beats are quarter-note beats in 4/4 (1 = downbeat, 1.5 = the "and").
DRUM_PATTERNS = {
    "rock": {
        KICK: [1, 3],
        SNARE: [2, 4],
        HIHAT_CLOSED: [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5],
    },
    "jazz": {
        RIDE: [1, 2, 3, 4],
        KICK: [1],
        SNARE: [2.5, 4.5],
        HIHAT_CLOSED: [2, 4],
    },
    "pop": {
        KICK: [1, 2.5, 3],
        SNARE: [2, 4],
        HIHAT_CLOSED: [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5],
    },
    "latin": {
        KICK: [1, 2.5, 4],
        SNARE: [2, 3.5],
        HIHAT_CLOSED: [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5],
    },
    "metal": {
        KICK: [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5],
        SNARE: [2, 4],
        HIHAT_CLOSED: [
            1, 1.25, 1.5, 1.75,
            2, 2.25, 2.5, 2.75,
            3, 3.25, 3.5, 3.75,
            4, 4.25, 4.5, 4.75,
        ],
    },
}


def key_signature_name(fifths: int) -> str:
    return KEY_FIFTHS.get(int(fifths), "C")


def note_name_to_midi(note_name: str) -> int:
    """Convert a note name such as 'C4' or 'F#5' to a MIDI pitch."""
    if MUSIC21_AVAILABLE:
        return pitch.Pitch(note_name).midi

    match = re.match(r"^([A-Ga-g])([#b♯♭]?)(-?\d+)$", note_name.strip())
    if not match:
        raise ValueError(f"Cannot read note name '{note_name}'")
    semitone = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}[match.group(1).upper()]
    accidental = _ACCIDENTALS.get(match.group(2), "")
    if accidental == "#":
        semitone += 1
    elif accidental == "b":
        semitone -= 1
    octave = int(match.group(3))
    return (octave + 1) * 12 + semitone


def midi_to_note_name(midi: int) -> str:
    if MUSIC21_AVAILABLE:
        return pitch.Pitch(midi=int(midi)).nameWithOctave
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    midi = int(midi)
    octave = (midi // 12) - 1
    return f"{names[midi % 12]}{octave}"


def parse_chord_symbol(symbol: str) -> Tuple[str, str]:
    """
    Parse a lead-sheet symbol into (root, quality).

    'Gmaj' is major. 'Gm' / 'Gmin' is minor. 'G7' is dominant seventh.
    """
    text = symbol.strip().replace(" ", "")
    match = re.match(r"^([A-Ga-g])([#b♯♭]?)(.*)$", text)
    if not match:
        raise ValueError(f"Cannot parse chord symbol '{symbol}'")

    root = match.group(1).upper() + _ACCIDENTALS.get(match.group(2), "")
    quality_text = match.group(3).lower()
    if quality_text.startswith("/"):
        return root, "major"

    if not quality_text:
        return root, "major"

    for suffix, quality in _QUALITIES:
        if quality_text == suffix or quality_text.startswith(suffix):
            rest = quality_text[len(suffix):]
            if rest == "" or rest.startswith("/"):
                return root, quality

    raise ValueError(f"Unknown chord quality in '{symbol}'")


def get_scale_pitches(root: str, scale_type: str = "major", octave: int = 4) -> List[int]:
    if MUSIC21_AVAILABLE:
        builders = {
            "major": scale.MajorScale,
            "minor": scale.MinorScale,
            "harmonic_minor": scale.HarmonicMinorScale,
            "melodic_minor": scale.MelodicMinorScale,
            "blues": scale.BluesScale,
            "pentatonic": scale.MajorPentatonicScale,
        }
        sc = builders.get(scale_type, scale.MajorScale)(root)
        return [p.midi for p in sc.getPitches(f"{root}{octave}", f"{root}{octave + 1}")]

    root_midi = note_name_to_midi(f"{root}{octave}")
    intervals = {
        "major": [0, 2, 4, 5, 7, 9, 11, 12],
        "minor": [0, 2, 3, 5, 7, 8, 10, 12],
        "harmonic_minor": [0, 2, 3, 5, 7, 8, 11, 12],
        "melodic_minor": [0, 2, 3, 5, 7, 9, 11, 12],
        "blues": [0, 3, 5, 6, 7, 10, 12],
        "pentatonic": [0, 2, 4, 7, 9, 12],
    }.get(scale_type, [0, 2, 4, 5, 7, 9, 11, 12])
    return [root_midi + step for step in intervals]


def get_chord_pitches(root: str, chord_type: str = "major", octave: int = 4) -> List[int]:
    root_midi = note_name_to_midi(f"{root}{octave}")
    intervals = _CHORD_INTERVALS.get(chord_type, _CHORD_INTERVALS["major"])
    return [root_midi + step for step in intervals]


def shift_root(root: str, semitones: int) -> str:
    """Move a chord root by semitones and return a name without the octave."""
    midi = note_name_to_midi(f"{root}4") + semitones
    return re.sub(r"-?\d+$", "", midi_to_note_name(midi))


def beat_to_tick(beat: float, ticks_for_beat: int = 480) -> int:
    return int(round((beat - 1) * ticks_for_beat))


def generate_walking_bass(
    chord_progression: List[Tuple[str, str]],
    measures: int,
    beats_per_measure: int = 4,
    ticks_for_beat: int = 480,
) -> List[dict]:
    """
    One chord tone per beat: root, third, fifth, then a chromatic approach
    into the next chord. The last beat of a bar walks to the next root.
    """
    if not chord_progression:
        raise ValueError("Walking bass needs at least one chord")

    notes = []
    bass_octave = 2
    for measure_idx in range(measures):
        chord_root, chord_type = chord_progression[measure_idx % len(chord_progression)]
        tones = get_chord_pitches(chord_root, chord_type, bass_octave)
        next_root, _ = chord_progression[(measure_idx + 1) % len(chord_progression)]
        approach = note_name_to_midi(f"{next_root}{bass_octave}") - 1

        for beat_index in range(beats_per_measure):
            if beat_index == 0:
                chosen = tones[0]
            elif beat_index == beats_per_measure - 1 and beats_per_measure > 1:
                chosen = approach
            elif beat_index == 1:
                chosen = tones[1] if len(tones) > 1 else tones[0]
            else:
                chosen = tones[2] if len(tones) > 2 else tones[0]

            chosen = max(0, min(127, chosen))
            notes.append({
                "type": "add_note",
                "pitch": chosen,
                "duration": ticks_for_beat,
                "measure": measure_idx,
                "tick": beat_index * ticks_for_beat,
                "track": 0,
            })
    return notes


def generate_drum_pattern(style: str, measures: int, track: int = 0) -> List[dict]:
    """
    Group kit hits that share a beat into one chord, and set each duration
    to the gap until the next hit so the bar fills exactly.
    """
    pattern = DRUM_PATTERNS.get(style, DRUM_PATTERNS["rock"])
    ticks_for_beat = 480
    bar_ticks = 1920
    commands = []

    for measure in range(measures):
        buckets: Dict[int, List[int]] = {}
        for drum_pitch, beats in pattern.items():
            for beat in beats:
                tick = beat_to_tick(beat, ticks_for_beat)
                if tick < 0 or tick >= bar_ticks:
                    continue
                buckets.setdefault(tick, [])
                if drum_pitch not in buckets[tick]:
                    buckets[tick].append(drum_pitch)

        ticks = sorted(buckets)
        for index, tick in enumerate(ticks):
            if index + 1 < len(ticks):
                duration = ticks[index + 1] - tick
            else:
                duration = bar_ticks - tick
            if duration <= 0:
                continue
            pitches = sorted(buckets[tick])
            command = {
                "type": "add_chord" if len(pitches) > 1 else "add_note",
                "duration": duration,
                "measure": measure,
                "tick": tick,
                "track": track,
                "drums": True,
            }
            if len(pitches) > 1:
                command["pitches"] = pitches
            else:
                command["pitch"] = pitches[0]
            commands.append(command)

    return commands


def generate_harmony(melody_pitches: List[int], interval_semitones: int = 4, direction: str = "above") -> List[int]:
    offset = interval_semitones if direction == "above" else -interval_semitones
    return [pitch_value + offset for pitch_value in melody_pitches]


def transpose_pitches(pitches: List[int], semitones: int) -> List[int]:
    return [pitch_value + semitones for pitch_value in pitches]


def analyze_key(pitches: List[int]) -> str:
    if not MUSIC21_AVAILABLE:
        return "C"
    part = stream.Stream()
    for midi in pitches:
        part.append(note.Note(midi=midi))
    return str(part.analyze("key"))


def describe_command(command: dict, time_signature: Tuple[int, int] = (4, 4)) -> str:
    """One readable line for a command. Bar numbers start at 1."""
    kind = command.get("type", "command")
    measure = int(command.get("measure", 0) or 0)
    bar = measure + 1
    denominator = time_signature[1] if time_signature else 4
    beat_ticks = ticks_per_beat(denominator)
    duration_name = _duration_name(command.get("duration"))

    def place() -> str:
        if command.get("tick") is None:
            return f"bar {bar}"
        beat = _format_beat(int(command.get("tick") or 0), beat_ticks)
        return f"bar {bar} beat {beat}"

    if kind in ("add_note", "add_chord", "add_rest"):
        if kind == "add_rest":
            name = f"{duration_name} rest"
        elif command.get("drums"):
            pitches = command.get("pitches") or [command.get("pitch")]
            name = " + ".join(GM_DRUMS.get(int(item), midi_to_note_name(int(item))) for item in pitches)
        elif kind == "add_chord":
            pitches = command.get("pitches") or []
            name = "chord " + " ".join(midi_to_note_name(int(item)) for item in pitches)
        else:
            name = "note " + midi_to_note_name(int(command["pitch"]))
        track = command.get("track", 0)
        return f"{name} · {place()} · {duration_name} · track {track}"

    if kind == "add_dynamic":
        return f"dynamic {command.get('dynamic', 'mf')} · bar {bar}"
    if kind == "add_tempo":
        text = command.get("text")
        label = f"tempo {command.get('bpm', '')}".strip()
        if text:
            label += f" ({text})"
        return f"{label} · bar {bar}"
    if kind == "add_text":
        return f"text \"{command.get('text', '')}\" · bar {bar}"
    if kind == "transpose":
        semitones = int(command.get("semitones", 0) or 0)
        direction = "up" if semitones > 0 else "down"
        return f"transpose {direction} {abs(semitones)} semitones"
    return kind


def _duration_name(ticks) -> str:
    from durations import NAME_BY_TICKS

    if ticks is None:
        return "quarter"
    return NAME_BY_TICKS.get(int(ticks), f"{int(ticks)} ticks")


def _format_beat(tick: int, ticks_for_beat: int) -> str:
    from durations import format_beat

    return format_beat(tick, ticks_for_beat)


class MusicGenerator:
    """High-level patterns turned into plugin commands."""

    def __init__(self, key_signature: str = "C", time_signature: Tuple[int, int] = (4, 4)):
        self.key = key_signature
        self.time_sig = time_signature
        self.ticks_per_beat = ticks_per_beat(time_signature[1])
        self.ticks_per_measure = measure_length(time_signature[0], time_signature[1])

    def walking_bass_line(self, chords: List[str], measures: int, track: int = 0) -> List[dict]:
        progression = [parse_chord_symbol(symbol) for symbol in chords]
        notes = generate_walking_bass(
            progression,
            measures,
            beats_per_measure=self.time_sig[0],
            ticks_for_beat=self.ticks_per_beat,
        )
        for command in notes:
            command["track"] = track
        return notes

    def drum_pattern(self, style: str, measures: int, track: int = 0) -> List[dict]:
        return generate_drum_pattern(style, measures, track=track)

    def add_harmony(self, melody_track: int, harmony_track: int, interval: str = "third_above") -> List[dict]:
        intervals = {
            "third_above": 4,
            "third_below": -3,
            "sixth_above": 9,
            "sixth_below": -4,
            "octave_above": 12,
            "octave_below": -12,
        }
        return [{
            "type": "harmonize",
            "source_track": melody_track,
            "target_track": harmony_track,
            "interval": intervals.get(interval, 4),
        }]


if __name__ == "__main__":
    gen = MusicGenerator(key_signature="G", time_signature=(4, 4))
    print("Walking bass:")
    for command in gen.walking_bass_line(["Gmaj", "C", "D7", "G"], measures=1):
        print(" ", describe_command(command))
    print("Rock drums:")
    for command in gen.drum_pattern("rock", measures=1)[:4]:
        print(" ", describe_command(command))
