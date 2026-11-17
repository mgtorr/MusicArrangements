#!/usr/bin/env python3
"""
Local theory engine.

Handles the requests people actually type when no model key is configured,
and when a model returns nothing useful. Bar numbers in the sentence start at 1.
Commands use measure 0 for the first bar.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from music_logic import (
    MusicGenerator,
    get_chord_pitches,
    key_signature_name,
    note_name_to_midi,
    parse_chord_symbol,
    shift_root,
)

_CHORD_TOKEN = re.compile(
    r"\b([A-G](?:#|b|♯|♭)?(?:maj7|min7|m7|dim7|sus2|sus4|add9|maj|min|dim|aug|m|7)?)\b",
    re.IGNORECASE,
)

_CHORD_PHRASE = re.compile(
    r"\b([A-G](?:#|b|♯|♭)?)(\d)?\s+"
    r"(major seventh|minor seventh|dominant seventh|diminished|augmented|"
    r"major|minor|maj7|min7|m7|sus2|sus4|dim|aug|7)"
    r"\s+chord\b",
    re.IGNORECASE,
)

_NOTE = re.compile(
    r"\b([A-G](?:#|b|♯|♭)?)(-?\d)\b",
    re.IGNORECASE,
)

_STYLES = ("metal", "latin", "jazz", "rock", "pop")

_INTERVALS = [
    ("minor second", 1),
    ("major second", 2),
    ("minor third", 3),
    ("major third", 4),
    ("perfect fourth", 5),
    ("tritone", 6),
    ("perfect fifth", 7),
    ("minor sixth", 8),
    ("major sixth", 9),
    ("minor seventh", 10),
    ("major seventh", 11),
    ("octave", 12),
    ("second", 2),
    ("third", 4),
    ("fourth", 5),
    ("fifth", 7),
    ("sixth", 9),
    ("seventh", 11),
]

_QUALITY_WORDS = {
    "major seventh": "maj7",
    "minor seventh": "min7",
    "dominant seventh": "dom7",
    "diminished": "dim",
    "augmented": "aug",
    "major": "major",
    "minor": "minor",
    "maj7": "maj7",
    "min7": "min7",
    "m7": "min7",
    "sus2": "sus2",
    "sus4": "sus4",
    "dim": "dim",
    "aug": "aug",
    "7": "dom7",
}

_DYNAMIC_WORDS = [
    ("mezzo piano", "mp"),
    ("mezzo-piano", "mp"),
    ("mezzo forte", "mf"),
    ("mezzo-forte", "mf"),
    ("pianissimo", "pp"),
    ("fortissimo", "ff"),
    ("sforzando", "sfz"),
    ("piano", "p"),
    ("forte", "f"),
]

_DURATION_WORDS = [
    ("dotted half", 1440),
    ("dotted quarter", 720),
    ("dotted eighth", 360),
    ("sixteenth", 120),
    ("16th", 120),
    ("whole", 1920),
    ("quarter", 480),
    ("eighth", 240),
    ("half", 960),
]


@dataclass
class LocalResponse:
    intent: str
    commands: List[dict] = field(default_factory=list)
    notes: str = ""


def interpret_locally(user_request: str, score_context: Optional[dict] = None) -> LocalResponse:
    text = (user_request or "").strip()
    if not text:
        return LocalResponse("Empty request", notes="Type a change, for example: Add a C major chord at the beginning.")

    generator = _generator(score_context)
    lowered = text.lower()

    if "walking bass" in lowered:
        return _walking_bass(text, generator)
    if re.search(r"\bdrums?\b", lowered):
        return _drums(text, generator)
    if "transpose" in lowered:
        return _transpose(text)
    if "tempo" in lowered or re.search(r"\bbpm\b", lowered):
        return _tempo(text)
    dynamic = _dynamic(text, words_only=True)
    if dynamic is not None:
        return dynamic
    if "chord" in lowered:
        return _chord(text, generator, score_context)
    if _NOTE.search(text) and "rest" not in lowered:
        return _note(text)
    dynamic = _dynamic(text, words_only=False)
    if dynamic is not None:
        return dynamic
    if "rest" in lowered:
        return _rest(text)

    return LocalResponse(
        "Not understood",
        notes=(
            "The local theory engine knows chords, notes, rests, dynamics, tempo, "
            "transpose, walking bass, and drum patterns. "
            "Try: Add a C major chord at the beginning. "
            "Transpose up a perfect fifth. "
            "Walking bass G C D G for 4 measures. "
            "Rock drums for 4 measures."
        ),
    )


def _generator(score_context: Optional[dict]) -> MusicGenerator:
    time_sig = (4, 4)
    key_name = "C"
    if score_context:
        signature = score_context.get("time_signature") or {}
        if signature:
            time_sig = (
                int(signature.get("numerator") or 4),
                int(signature.get("denominator") or 4),
            )
        fifths = score_context.get("key_signature")
        if isinstance(fifths, int):
            key_name = key_signature_name(fifths)
        elif isinstance(fifths, str) and fifths:
            key_name = fifths
    return MusicGenerator(key_name, time_sig)


def _key_root(score_context: Optional[dict], generator: MusicGenerator) -> str:
    if score_context and isinstance(score_context.get("key_signature"), int):
        return key_signature_name(score_context["key_signature"])
    return generator.key or "C"


def _walking_bass(text: str, generator: MusicGenerator) -> LocalResponse:
    after = re.split(r"walking bass(?:\s+line)?", text, maxsplit=1, flags=re.IGNORECASE)[-1]
    chords = []
    for match in _CHORD_TOKEN.finditer(after):
        token = match.group(1)
        normalized = token[0].upper() + token[1:]
        try:
            parse_chord_symbol(normalized)
        except ValueError:
            continue
        chords.append(normalized)

    # Drop the measure count if the regex ever treated it as a token (it does not).
    if not chords:
        return LocalResponse(
            "Walking bass",
            notes="Name the chords. Example: walking bass G C D G for 4 measures.",
        )

    measures = _measure_count(text, default=len(chords))
    track = _track(text)
    try:
        commands = generator.walking_bass_line(chords, measures, track=track)
    except ValueError as exc:
        return LocalResponse("Walking bass", notes=str(exc))

    return LocalResponse(
        f"Walking bass on {' '.join(chords)} for {measures} bars",
        commands,
        notes="One chord tone per beat, with a chromatic step into the next chord on the last beat.",
    )


def _drums(text: str, generator: MusicGenerator) -> LocalResponse:
    style = "rock"
    lowered = text.lower()
    for name in _STYLES:
        if re.search(rf"\b{name}\b", lowered):
            style = name
            break
    measures = _measure_count(text, default=4)
    track = _track(text)
    commands = generator.drum_pattern(style, measures, track=track)
    notes = "Hits that share a beat are written together, and the bar is filled in time."
    if generator.time_sig != (4, 4):
        notes += " These patterns are written in 4/4."
    return LocalResponse(
        f"{style.capitalize()} drums for {measures} bars",
        commands,
        notes=notes,
    )


def _transpose(text: str) -> LocalResponse:
    steps = _semitones(text)
    if steps is None:
        return LocalResponse(
            "Transpose",
            notes="Say the interval or the semitones. Example: transpose up a perfect fifth.",
        )
    if steps == 0:
        return LocalResponse("Transpose", notes="That transposition does not move any notes.")
    direction = "up" if steps > 0 else "down"
    return LocalResponse(
        f"Transpose {direction} {abs(steps)} semitones",
        [{"type": "transpose", "semitones": steps}],
        notes="Every note in the score moves, including drum staves. Undo if the kit should stay put.",
    )


def _semitones(text: str) -> Optional[int]:
    lowered = text.lower()
    direction = -1 if re.search(r"\bdown\b", lowered) else 1
    match = re.search(r"([+-]?\d+)\s*semitones?", lowered)
    if match:
        steps = int(match.group(1))
        if re.search(r"\bdown\b", lowered) and steps > 0:
            return -steps
        if re.search(r"\bup\b", lowered) and steps < 0:
            return abs(steps)
        return steps
    for name, size in _INTERVALS:
        if name in lowered:
            return size * direction
    return None


def _tempo(text: str) -> LocalResponse:
    match = re.search(r"\b(\d{2,3})\b", text)
    if not match:
        return LocalResponse("Tempo", notes="Include a speed, for example: set the tempo to 96.")
    bpm = int(match.group(1))
    measure = _bar_index(text)
    return LocalResponse(
        f"Tempo {bpm}",
        [{"type": "add_tempo", "bpm": bpm, "measure": measure}],
        notes=f"Tempo marking at bar {measure + 1}.",
    )


def _dynamic(text: str, words_only: bool = False) -> Optional[LocalResponse]:
    lowered = text.lower()
    marking = None
    for word, value in _DYNAMIC_WORDS:
        if word in lowered:
            marking = value
            break
    if marking is None and not words_only:
        # Accidentals such as F# must not be read as the dynamic "f".
        match = re.search(r"\b(pppp|ppp|pp|mp|mf|sfz|fp|fff|ffff|ff|p|f)(?![#b♯♭\d])", lowered)
        if match and (
            re.search(r"\b(dynamic|add|mark)\b", lowered)
            or re.search(r"\b(pppp|ppp|pp|mp|mf|sfz|ff)\b", lowered)
        ):
            marking = match.group(1)
    if marking is None:
        return None
    measure = _bar_index(text)
    return LocalResponse(
        f"Dynamic {marking}",
        [{"type": "add_dynamic", "dynamic": marking, "measure": measure, "track": _track(text)}],
        notes=f"Dynamic at bar {measure + 1}.",
    )


def _chord(text: str, generator: MusicGenerator, score_context: Optional[dict]) -> LocalResponse:
    function = re.search(r"\b(tonic|dominant|subdominant)\s+chord\b", text, re.IGNORECASE)
    if function:
        root = _key_root(score_context, generator)
        kind = function.group(1).lower()
        if kind == "dominant":
            root = shift_root(root, 7)
        elif kind == "subdominant":
            root = shift_root(root, 5)
        quality = "major"
        described = f"{root} {quality}"
    else:
        match = _CHORD_PHRASE.search(text)
        if not match:
            symbol = re.search(
                r"\bchord\s+([A-G](?:#|b|♯|♭)?(?:maj7|min7|m7|dim7|sus2|sus4|add9|maj|min|dim|aug|m|7)?)\b",
                text,
                re.IGNORECASE,
            )
            if not symbol:
                return LocalResponse(
                    "Chord",
                    notes="Name the chord. Example: Add a C major chord at the beginning.",
                )
            root, quality = parse_chord_symbol(symbol.group(1))
            octave = 4
            described = symbol.group(1)
            duration = _duration(text, default=480)
            measure = _bar_index(text)
            pitches = get_chord_pitches(root, quality, octave)
            return _chord_response(described, pitches, duration, measure, text)

        root = match.group(1)[0].upper() + match.group(1)[1:]
        octave = int(match.group(2)) if match.group(2) else 4
        quality = _QUALITY_WORDS[match.group(3).lower()]
        described = f"{root}{match.group(2) or ''} {match.group(3)}"
        duration = _duration(text, default=480)
        measure = _bar_index(text)
        pitches = get_chord_pitches(root, quality, octave)
        return _chord_response(described, pitches, duration, measure, text)

    duration = _duration(text, default=480)
    measure = _bar_index(text)
    pitches = get_chord_pitches(root, quality, 4)
    return _chord_response(described, pitches, duration, measure, text)


def _chord_response(described: str, pitches: List[int], duration: int, measure: int, text: str) -> LocalResponse:
    from durations import NAME_BY_TICKS

    length = NAME_BY_TICKS.get(duration, "note")
    return LocalResponse(
        f"Add {described} chord",
        [{
            "type": "add_chord",
            "pitches": pitches,
            "duration": duration,
            "measure": measure,
            "tick": 0,
            "track": _track(text),
        }],
        notes=f"{length.capitalize()} chord on beat 1 of bar {measure + 1}.",
    )


def _note(text: str) -> LocalResponse:
    match = _NOTE.search(text)
    if not match:
        return LocalResponse("Note", notes="Name the note with an octave, for example C4 or F#3.")
    name = match.group(1)[0].upper() + match.group(1)[1:] + match.group(2)
    try:
        midi = note_name_to_midi(name)
    except ValueError as exc:
        return LocalResponse("Note", notes=str(exc))
    duration = _duration(text, default=480)
    measure = _bar_index(text)
    from durations import NAME_BY_TICKS

    length = NAME_BY_TICKS.get(duration, "note")
    return LocalResponse(
        f"Add {name}",
        [{
            "type": "add_note",
            "pitch": midi,
            "duration": duration,
            "measure": measure,
            "tick": 0,
            "track": _track(text),
        }],
        notes=f"{length.capitalize()} note on beat 1 of bar {measure + 1}.",
    )


def _rest(text: str) -> LocalResponse:
    duration = _duration(text, default=480)
    measure = _bar_index(text)
    from durations import NAME_BY_TICKS

    length = NAME_BY_TICKS.get(duration, "rest")
    return LocalResponse(
        f"Add a {length} rest",
        [{
            "type": "add_rest",
            "duration": duration,
            "measure": measure,
            "tick": 0,
            "track": _track(text),
        }],
        notes=f"Rest on beat 1 of bar {measure + 1}.",
    )


def _measure_count(text: str, default: int = 4) -> int:
    match = re.search(r"\b(\d+)\s*measures?\b", text, re.IGNORECASE)
    if not match:
        match = re.search(r"\b(\d+)\s*bars?\b", text, re.IGNORECASE)
    if not match:
        return default
    return max(1, min(int(match.group(1)), 256))


def _bar_index(text: str) -> int:
    """Spoken bar numbers start at 1. Command measures start at 0."""
    match = re.search(r"\b(?:measure|bar)\s+(\d+)\b", text, re.IGNORECASE)
    if not match:
        return 0
    number = int(match.group(1))
    if number <= 0:
        return 0
    return number - 1


def _duration(text: str, default: int) -> int:
    lowered = text.lower()
    for word, ticks in _DURATION_WORDS:
        if word in lowered:
            return ticks
    return default


def _track(text: str) -> int:
    match = re.search(r"\btrack\s+(\d+)\b", text, re.IGNORECASE)
    if not match:
        return 0
    return max(0, int(match.group(1)))
