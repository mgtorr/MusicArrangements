#!/usr/bin/env python3
"""
Music Logic Module - Uses Music21 for musical calculations
Translates high-level musical concepts into atomic MuseScore commands
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from music21 import pitch, interval, scale, chord, key, meter, tempo, stream, note, duration
    MUSIC21_AVAILABLE = True
except ImportError:
    MUSIC21_AVAILABLE = False
    print("Warning: music21 not installed. Install with: pip install music21")


# Duration constants (in MuseScore ticks, 480 = quarter note)
class Duration(Enum):
    WHOLE = 1920
    HALF = 960
    QUARTER = 480
    EIGHTH = 240
    SIXTEENTH = 120
    THIRTYSECOND = 60
    DOTTED_HALF = 1440
    DOTTED_QUARTER = 720
    DOTTED_EIGHTH = 360


# MIDI pitch constants
MIDDLE_C = 60  # C4


@dataclass
class NoteEvent:
    """A single note event"""
    pitch: int  # MIDI pitch
    duration: int  # Ticks
    measure: int
    beat: float
    track: int = 0
    velocity: int = 80


@dataclass
class ChordEvent:
    """A chord event"""
    pitches: List[int]
    duration: int
    measure: int
    beat: float
    track: int = 0


def note_name_to_midi(note_name: str) -> int:
    """Convert note name (e.g., 'C4', 'F#5') to MIDI pitch"""
    if MUSIC21_AVAILABLE:
        p = pitch.Pitch(note_name)
        return p.midi
    else:
        # Simple fallback
        note_map = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
        name = note_name[0].upper()
        octave = int(note_name[-1])
        midi = (octave + 1) * 12 + note_map.get(name, 0)
        if '#' in note_name:
            midi += 1
        elif 'b' in note_name:
            midi -= 1
        return midi


def midi_to_note_name(midi: int) -> str:
    """Convert MIDI pitch to note name"""
    if MUSIC21_AVAILABLE:
        p = pitch.Pitch(midi=midi)
        return p.nameWithOctave
    else:
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi // 12) - 1
        note_idx = midi % 12
        return f"{note_names[note_idx]}{octave}"


def get_scale_pitches(root: str, scale_type: str = "major", octave: int = 4) -> List[int]:
    """Get MIDI pitches for a scale"""
    if MUSIC21_AVAILABLE:
        if scale_type == "major":
            sc = scale.MajorScale(root)
        elif scale_type == "minor":
            sc = scale.MinorScale(root)
        elif scale_type == "harmonic_minor":
            sc = scale.HarmonicMinorScale(root)
        elif scale_type == "melodic_minor":
            sc = scale.MelodicMinorScale(root)
        elif scale_type == "blues":
            sc = scale.BluesScale(root)
        elif scale_type == "pentatonic":
            sc = scale.MajorPentatonicScale(root)
        else:
            sc = scale.MajorScale(root)

        pitches = []
        for p in sc.getPitches(f"{root}{octave}", f"{root}{octave + 1}"):
            pitches.append(p.midi)
        return pitches
    else:
        # Fallback: major scale intervals
        root_midi = note_name_to_midi(f"{root}{octave}")
        intervals = [0, 2, 4, 5, 7, 9, 11, 12]  # Major scale
        return [root_midi + i for i in intervals]


def get_chord_pitches(root: str, chord_type: str = "major", octave: int = 4) -> List[int]:
    """Get MIDI pitches for a chord"""
    root_midi = note_name_to_midi(f"{root}{octave}")

    chord_intervals = {
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

    intervals = chord_intervals.get(chord_type, chord_intervals["major"])
    return [root_midi + i for i in intervals]


def generate_walking_bass(
    key_root: str,
    chord_progression: List[Tuple[str, str]],  # [(root, type), ...]
    measures: int,
    beats_per_measure: int = 4
) -> List[NoteEvent]:
    """
    Generate a walking bass line

    Args:
        key_root: Key of the piece (e.g., "G")
        chord_progression: List of (root, chord_type) tuples
        measures: Number of measures
        beats_per_measure: Beats per measure (usually 4)

    Returns:
        List of NoteEvent for the bass line
    """
    notes = []
    bass_octave = 2  # Bass register

    for measure_idx in range(measures):
        chord_idx = measure_idx % len(chord_progression)
        chord_root, chord_type = chord_progression[chord_idx]

        # Get chord tones
        chord_pitches = get_chord_pitches(chord_root, chord_type, bass_octave)

        # Walking bass pattern: root, 3rd, 5th, approach note
        for beat in range(beats_per_measure):
            if beat == 0:
                pitch_val = chord_pitches[0]  # Root
            elif beat == 1:
                pitch_val = chord_pitches[1] if len(chord_pitches) > 1 else chord_pitches[0]  # 3rd
            elif beat == 2:
                pitch_val = chord_pitches[2] if len(chord_pitches) > 2 else chord_pitches[0]  # 5th
            else:
                # Approach note to next chord
                next_chord_idx = (chord_idx + 1) % len(chord_progression)
                next_root, _ = chord_progression[next_chord_idx]
                next_root_pitch = note_name_to_midi(f"{next_root}{bass_octave}")
                # Chromatic approach from below
                pitch_val = next_root_pitch - 1

            notes.append(NoteEvent(
                pitch=pitch_val,
                duration=Duration.QUARTER.value,
                measure=measure_idx,
                beat=beat + 1,
                track=0
            ))

    return notes


def generate_drum_pattern(
    style: str,
    measures: int,
    beats_per_measure: int = 4
) -> List[NoteEvent]:
    """
    Generate a drum pattern

    Note: MuseScore uses specific MIDI pitches for drums (GM standard)
    """
    # GM Drum Map
    KICK = 36
    SNARE = 38
    HIHAT_CLOSED = 42
    HIHAT_OPEN = 46
    RIDE = 51
    CRASH = 49

    patterns = {
        "rock": {
            KICK: [1, 3],  # Beats where kick plays
            SNARE: [2, 4],
            HIHAT_CLOSED: [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5]
        },
        "jazz": {
            RIDE: [1, 2, 3, 4],
            KICK: [1],
            SNARE: [2.5, 4.5],
            HIHAT_CLOSED: [2, 4]
        },
        "pop": {
            KICK: [1, 2.5, 3],
            SNARE: [2, 4],
            HIHAT_CLOSED: [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5]
        },
        "latin": {
            KICK: [1, 2.5, 4],
            SNARE: [2, 3.5],
            HIHAT_CLOSED: [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5]
        },
        "metal": {
            KICK: [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5],
            SNARE: [2, 4],
            HIHAT_CLOSED: [1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75, 3, 3.25, 3.5, 3.75, 4, 4.25, 4.5, 4.75]
        }
    }

    pattern = patterns.get(style, patterns["rock"])
    notes = []

    for measure in range(measures):
        for drum_pitch, beats in pattern.items():
            for beat in beats:
                # Calculate duration based on beat subdivision
                dur = Duration.EIGHTH.value if beat != int(beat) else Duration.QUARTER.value

                notes.append(NoteEvent(
                    pitch=drum_pitch,
                    duration=dur,
                    measure=measure,
                    beat=beat,
                    track=0  # Drum track
                ))

    return notes


def generate_harmony(
    melody_pitches: List[int],
    interval_semitones: int = 4,  # Major 3rd by default
    direction: str = "above"
) -> List[int]:
    """Generate harmony line parallel to melody"""
    offset = interval_semitones if direction == "above" else -interval_semitones
    return [p + offset for p in melody_pitches]


def transpose_pitches(pitches: List[int], semitones: int) -> List[int]:
    """Transpose a list of pitches by semitones"""
    return [p + semitones for p in pitches]


def analyze_key(pitches: List[int]) -> str:
    """Analyze likely key from a list of pitches"""
    if not MUSIC21_AVAILABLE:
        return "C"  # Default fallback

    # Create a stream with the notes
    s = stream.Stream()
    for p in pitches:
        n = note.Note(midi=p)
        s.append(n)

    # Analyze key
    analysis = s.analyze('key')
    return str(analysis)


def get_duration_ticks(duration_name: str) -> int:
    """Convert duration name to ticks"""
    duration_map = {
        "whole": Duration.WHOLE.value,
        "half": Duration.HALF.value,
        "quarter": Duration.QUARTER.value,
        "eighth": Duration.EIGHTH.value,
        "16th": Duration.SIXTEENTH.value,
        "32nd": Duration.THIRTYSECOND.value,
        "dotted_half": Duration.DOTTED_HALF.value,
        "dotted_quarter": Duration.DOTTED_QUARTER.value,
        "dotted_eighth": Duration.DOTTED_EIGHTH.value,
    }
    return duration_map.get(duration_name.lower(), Duration.QUARTER.value)


class MusicGenerator:
    """High-level music generation class"""

    def __init__(self, key_signature: str = "C", time_signature: Tuple[int, int] = (4, 4)):
        self.key = key_signature
        self.time_sig = time_signature
        self.ticks_per_beat = 480
        self.ticks_per_measure = self.ticks_per_beat * time_signature[0]

    def walking_bass_line(self, chords: List[str], measures: int) -> List[Dict]:
        """
        Generate walking bass commands

        Args:
            chords: List of chord symbols like ["Gmaj", "Cmaj", "Dmin", "Gmaj"]
            measures: Number of measures

        Returns:
            List of command dictionaries
        """
        # Parse chord symbols
        chord_progression = []
        for chord_sym in chords:
            if "min" in chord_sym.lower() or "m" in chord_sym:
                root = chord_sym.replace("min", "").replace("m", "").strip()
                chord_progression.append((root, "minor"))
            elif "dim" in chord_sym.lower():
                root = chord_sym.replace("dim", "").strip()
                chord_progression.append((root, "dim"))
            elif "aug" in chord_sym.lower():
                root = chord_sym.replace("aug", "").strip()
                chord_progression.append((root, "aug"))
            elif "7" in chord_sym:
                root = chord_sym.replace("7", "").replace("maj", "").strip()
                chord_progression.append((root, "dom7"))
            else:
                root = chord_sym.replace("maj", "").strip()
                chord_progression.append((root, "major"))

        notes = generate_walking_bass(self.key, chord_progression, measures, self.time_sig[0])

        commands = []
        for n in notes:
            commands.append({
                "type": "add_note",
                "pitch": n.pitch,
                "duration": n.duration,
                "measure": n.measure,
                "track": n.track
            })

        return commands

    def drum_pattern(self, style: str, measures: int) -> List[Dict]:
        """Generate drum pattern commands"""
        notes = generate_drum_pattern(style, measures, self.time_sig[0])

        commands = []
        for n in notes:
            commands.append({
                "type": "add_note",
                "pitch": n.pitch,
                "duration": n.duration,
                "measure": n.measure,
                "track": n.track
            })

        return commands

    def add_harmony(self, melody_track: int, harmony_track: int,
                    interval: str = "third_above") -> List[Dict]:
        """Generate harmony based on melody"""
        intervals = {
            "third_above": 4,
            "third_below": -3,
            "sixth_above": 9,
            "sixth_below": -4,
            "octave_above": 12,
            "octave_below": -12
        }

        # This would need the actual melody notes from the score
        # For now, return a template
        return [{
            "type": "harmonize",
            "source_track": melody_track,
            "target_track": harmony_track,
            "interval": intervals.get(interval, 4)
        }]


# Test
if __name__ == "__main__":
    gen = MusicGenerator(key_signature="G", time_signature=(4, 4))

    print("Walking bass commands:")
    bass_cmds = gen.walking_bass_line(["G", "C", "D", "G"], measures=4)
    for cmd in bass_cmds[:8]:
        print(f"  {cmd}")

    print("\nDrum pattern commands:")
    drum_cmds = gen.drum_pattern("rock", measures=2)
    for cmd in drum_cmds[:8]:
        print(f"  {cmd}")
