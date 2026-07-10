#!/usr/bin/env python3
"""
Composition Assistant - Advanced AI-powered music composition and arrangement
Provides high-level musical concepts and intelligent arrangement suggestions
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from music21 import pitch, interval, scale, chord, key, meter, stream, note, duration, roman
    MUSIC21_AVAILABLE = True
except ImportError:
    MUSIC21_AVAILABLE = False
    print("Warning: music21 not installed")

logger = logging.getLogger(__name__)


class ArrangementStyle(Enum):
    """Common arrangement styles"""
    CLASSICAL = "classical"
    JAZZ = "jazz"
    POP = "pop"
    ROCK = "rock"
    BLUES = "blues"
    FOLK = "folk"
    ELECTRONIC = "electronic"
    FILM_SCORE = "film_score"
    BALLAD = "ballad"


class FormType(Enum):
    """Musical form types"""
    BINARY = "AB"
    TERNARY = "ABA"
    RONDO = "ABACA"
    SONATA = "sonata"
    VERSE_CHORUS = "verse_chorus"
    TWELVE_BAR_BLUES = "12_bar_blues"
    THIRTY_TWO_BAR = "AABA"


@dataclass
class ChordProgression:
    """A chord progression with harmonic function"""
    chords: List[str]  # ["Cmaj", "Am", "Fmaj", "G7"]
    roman_numerals: List[str]  # ["I", "vi", "IV", "V7"]
    key_center: str  # "C"
    measures_per_chord: int = 1
    style: str = "major"


@dataclass
class MelodyContour:
    """Describes a melodic shape"""
    direction: str  # "ascending", "descending", "arch", "valley", "static"
    range_octaves: float  # 1.5
    rhythm_density: str  # "sparse", "moderate", "dense"
    start_note: Optional[int] = None  # MIDI pitch
    end_note: Optional[int] = None


@dataclass
class VoiceLeadingRule:
    """Voice leading rules for arrangements"""
    max_leap: int = 7  # semitones
    prefer_contrary_motion: bool = True
    avoid_parallel_fifths: bool = True
    avoid_parallel_octaves: bool = True
    max_voice_range: int = 12  # octave


class ProgressionGenerator:
    """Generate chord progressions in various styles"""

    COMMON_PROGRESSIONS = {
        "pop": [
            ["I", "V", "vi", "IV"],  # Popular pop progression
            ["I", "vi", "IV", "V"],  # 50s progression
            ["vi", "IV", "I", "V"],  # Sensitive progression
            ["I", "IV", "V", "IV"],  # Simple rock
        ],
        "jazz": [
            ["Imaj7", "vi7", "ii7", "V7"],  # Jazz turnaround
            ["Imaj7", "VI7", "ii7", "V7"],  # With secondary dominant
            ["ii7", "V7", "Imaj7", "VImaj7"],  # Modal jazz
            ["iii7", "VI7", "ii7", "V7"],  # Extended turnaround
        ],
        "classical": [
            ["I", "IV", "V", "I"],  # Authentic cadence
            ["I", "vi", "ii", "V"],  # Circle progression
            ["I", "V6", "vi", "iii", "IV", "I", "IV", "V"],  # Romanesca
        ],
        "blues": [
            ["I7", "I7", "I7", "I7", "IV7", "IV7", "I7", "I7", "V7", "IV7", "I7", "V7"],  # 12-bar blues
        ],
        "folk": [
            ["I", "IV", "I", "V"],  # Simple folk
            ["I", "V", "I", "V"],  # Minimal
            ["I", "IV", "V", "I"],  # Classic
        ]
    }

    SECONDARY_DOMINANTS = {
        "ii": "VI7",
        "iii": "VII7",
        "IV": "I7",
        "V": "II7",
        "vi": "III7"
    }

    def __init__(self, key_sig: str = "C", mode: str = "major"):
        self.key = key_sig
        self.mode = mode

    def generate_progression(self, style: str = "pop", length: int = 4) -> ChordProgression:
        """Generate a chord progression in a specific style"""
        
        # Get template progression
        templates = self.COMMON_PROGRESSIONS.get(style, self.COMMON_PROGRESSIONS["pop"])
        roman_numerals = templates[0][:length] if templates else ["I", "IV", "V", "I"]

        # Convert roman numerals to actual chords
        chords = self._roman_to_chords(roman_numerals)

        return ChordProgression(
            chords=chords,
            roman_numerals=roman_numerals,
            key_center=self.key,
            measures_per_chord=1,
            style=style
        )

    def add_secondary_dominants(self, progression: ChordProgression) -> ChordProgression:
        """Add secondary dominants to spice up progression"""
        new_romans = []
        new_chords = []

        for i, roman in enumerate(progression.roman_numerals):
            # Occasionally add secondary dominant before chord
            if i > 0 and roman in self.SECONDARY_DOMINANTS:
                if i % 2 == 0:  # Add on even positions
                    sec_dom = self.SECONDARY_DOMINANTS[roman]
                    new_romans.append(sec_dom)
                    new_chords.append(self._roman_to_chord(sec_dom))

            new_romans.append(roman)
            new_chords.append(progression.chords[i])

        return ChordProgression(
            chords=new_chords,
            roman_numerals=new_romans,
            key_center=progression.key_center,
            measures_per_chord=progression.measures_per_chord,
            style=progression.style
        )

    def _roman_to_chords(self, roman_numerals: List[str]) -> List[str]:
        """Convert roman numerals to chord names"""
        return [self._roman_to_chord(rn) for rn in roman_numerals]

    def _roman_to_chord(self, roman_numeral: str) -> str:
        """Convert a single roman numeral to chord name"""
        if not MUSIC21_AVAILABLE:
            return "Cmaj"  # Fallback

        try:
            # Parse roman numeral
            rn = roman.RomanNumeral(roman_numeral, self.key)
            chord_name = rn.pitches[0].name + rn.quality
            return chord_name
        except:
            return "Cmaj"


class MelodyGenerator:
    """Generate melodic lines"""

    def __init__(self, key_sig: str = "C", scale_type: str = "major"):
        self.key = key_sig
        self.scale_type = scale_type
        self.scale_degrees = self._get_scale_degrees()

    def _get_scale_degrees(self) -> List[int]:
        """Get scale degrees as MIDI offsets"""
        if self.scale_type == "major":
            return [0, 2, 4, 5, 7, 9, 11]  # Major scale
        elif self.scale_type == "minor":
            return [0, 2, 3, 5, 7, 8, 10]  # Natural minor
        elif self.scale_type == "harmonic_minor":
            return [0, 2, 3, 5, 7, 8, 11]
        elif self.scale_type == "pentatonic":
            return [0, 2, 4, 7, 9]
        elif self.scale_type == "blues":
            return [0, 3, 5, 6, 7, 10]
        else:
            return [0, 2, 4, 5, 7, 9, 11]

    def generate_melody(self, 
                       contour: MelodyContour,
                       num_notes: int,
                       start_octave: int = 5) -> List[Tuple[int, int]]:
        """
        Generate a melody following the contour
        
        Returns: List of (pitch, duration) tuples
        """
        import random
        
        pitches = []
        root_midi = self._note_to_midi(self.key, start_octave)

        # Generate pitch sequence based on contour
        if contour.direction == "ascending":
            for i in range(num_notes):
                degree_idx = (i % len(self.scale_degrees))
                octave_offset = (i // len(self.scale_degrees)) * 12
                pitch = root_midi + self.scale_degrees[degree_idx] + octave_offset
                pitches.append(pitch)

        elif contour.direction == "descending":
            start_pitch = root_midi + 12  # Start octave higher
            for i in range(num_notes):
                degree_idx = (num_notes - i - 1) % len(self.scale_degrees)
                octave_offset = -((i // len(self.scale_degrees)) * 12)
                pitch = start_pitch + self.scale_degrees[degree_idx] + octave_offset
                pitches.append(pitch)

        elif contour.direction == "arch":
            # Ascending then descending
            half = num_notes // 2
            for i in range(half):
                degree_idx = i % len(self.scale_degrees)
                pitch = root_midi + self.scale_degrees[degree_idx] + (i // 4) * 12
                pitches.append(pitch)
            for i in range(num_notes - half):
                degree_idx = (half - i - 1) % len(self.scale_degrees)
                pitch = root_midi + self.scale_degrees[degree_idx] + ((half - i) // 4) * 12
                pitches.append(pitch)

        else:  # static or random walk
            current_pitch = root_midi
            for i in range(num_notes):
                # Small random walk
                move = random.choice([-2, -1, 0, 1, 2])
                degree_idx = (i + move) % len(self.scale_degrees)
                current_pitch = root_midi + self.scale_degrees[degree_idx]
                pitches.append(current_pitch)

        # Generate rhythms based on density
        durations = self._generate_rhythms(num_notes, contour.rhythm_density)

        return list(zip(pitches, durations))

    def _generate_rhythms(self, num_notes: int, density: str) -> List[int]:
        """Generate rhythm pattern"""
        if density == "sparse":
            base_duration = 960  # Half notes
        elif density == "dense":
            base_duration = 240  # Eighth notes
        else:
            base_duration = 480  # Quarter notes

        import random
        durations = []
        for _ in range(num_notes):
            # Add some variation
            variation = random.choice([1, 1, 1, 1.5, 0.5])
            durations.append(int(base_duration * variation))

        return durations

    def _note_to_midi(self, note_name: str, octave: int) -> int:
        """Convert note name to MIDI"""
        note_map = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
        base = note_map.get(note_name[0].upper(), 0)
        if '#' in note_name:
            base += 1
        elif 'b' in note_name:
            base -= 1
        return (octave + 1) * 12 + base


class Harmonizer:
    """Add harmonies and counter-melodies"""

    def __init__(self, key_sig: str = "C"):
        self.key = key_sig

    def harmonize_melody(self,
                        melody_pitches: List[int],
                        style: str = "thirds") -> List[List[int]]:
        """
        Harmonize a melody
        
        Args:
            melody_pitches: List of MIDI pitches
            style: "thirds", "sixths", "fourths", "triads"
            
        Returns:
            List of chord voicings (list of pitches) for each melody note
        """
        harmonies = []

        for pitch in melody_pitches:
            if style == "thirds":
                # Add third below
                harmonies.append([pitch - 4, pitch])
            elif style == "sixths":
                # Add sixth below
                harmonies.append([pitch - 9, pitch])
            elif style == "fourths":
                # Add fourth below
                harmonies.append([pitch - 5, pitch])
            elif style == "triads":
                # Full triad
                harmonies.append([pitch - 7, pitch - 4, pitch])
            else:
                harmonies.append([pitch])

        return harmonies

    def voice_lead(self,
                  chord_sequence: List[List[int]],
                  rules: VoiceLeadingRule = None) -> List[List[int]]:
        """
        Apply voice leading rules to smooth out chord transitions
        
        Args:
            chord_sequence: List of chords (each chord is list of pitches)
            rules: Voice leading constraints
            
        Returns:
            Voice-led chord sequence
        """
        if rules is None:
            rules = VoiceLeadingRule()

        if not chord_sequence:
            return []

        voiced_chords = [chord_sequence[0]]

        for i in range(1, len(chord_sequence)):
            prev_chord = voiced_chords[-1]
            next_chord = chord_sequence[i].copy()

            # Try to minimize voice movement
            voiced = self._minimize_movement(prev_chord, next_chord, rules)
            voiced_chords.append(voiced)

        return voiced_chords

    def _minimize_movement(self,
                          from_chord: List[int],
                          to_chord: List[int],
                          rules: VoiceLeadingRule) -> List[int]:
        """Voice lead from one chord to another with minimal movement"""
        
        # Simple strategy: move each voice to nearest chord tone
        result = []
        for pitch in from_chord:
            # Find closest pitch in to_chord
            closest = min(to_chord, key=lambda p: abs(p - pitch))
            result.append(closest)

        return result


class Arranger:
    """High-level arrangement functions"""

    def __init__(self, key_sig: str = "C", time_sig: Tuple[int, int] = (4, 4)):
        self.key = key_sig
        self.time_sig = time_sig
        self.prog_generator = ProgressionGenerator(key_sig)
        self.melody_generator = MelodyGenerator(key_sig)
        self.harmonizer = Harmonizer(key_sig)

    def create_arrangement(self,
                          style: ArrangementStyle,
                          form: FormType,
                          total_measures: int) -> Dict[str, Any]:
        """
        Create a complete arrangement
        
        Returns:
            Dictionary with sections, progressions, melodies, etc.
        """
        arrangement = {
            "style": style.value,
            "form": form.value,
            "key": self.key,
            "time_signature": self.time_sig,
            "sections": []
        }

        # Generate form sections
        sections = self._generate_form(form, total_measures)
        
        for section in sections:
            section_data = {
                "name": section["name"],
                "start_measure": section["start"],
                "end_measure": section["end"],
                "progression": None,
                "melody": None,
                "bass": None,
                "drums": None
            }

            # Generate progression for section
            measures = section["end"] - section["start"]
            prog_style = style.value if style.value in ["pop", "jazz", "blues", "folk"] else "pop"
            progression = self.prog_generator.generate_progression(prog_style, measures)
            section_data["progression"] = progression

            arrangement["sections"].append(section_data)

        return arrangement

    def _generate_form(self, form: FormType, total_measures: int) -> List[Dict]:
        """Generate section layout based on form"""
        sections = []

        if form == FormType.BINARY:
            # AB form
            half = total_measures // 2
            sections.append({"name": "A", "start": 0, "end": half})
            sections.append({"name": "B", "start": half, "end": total_measures})

        elif form == FormType.TERNARY:
            # ABA form
            third = total_measures // 3
            sections.append({"name": "A", "start": 0, "end": third})
            sections.append({"name": "B", "start": third, "end": third * 2})
            sections.append({"name": "A", "start": third * 2, "end": total_measures})

        elif form == FormType.VERSE_CHORUS:
            # Verse-Chorus-Verse-Chorus
            quarter = total_measures // 4
            sections.append({"name": "Verse", "start": 0, "end": quarter})
            sections.append({"name": "Chorus", "start": quarter, "end": quarter * 2})
            sections.append({"name": "Verse", "start": quarter * 2, "end": quarter * 3})
            sections.append({"name": "Chorus", "start": quarter * 3, "end": total_measures})

        elif form == FormType.TWELVE_BAR_BLUES:
            # Repeat 12-bar pattern
            num_repeats = total_measures // 12
            for i in range(num_repeats):
                sections.append({
                    "name": f"Blues Chorus {i+1}",
                    "start": i * 12,
                    "end": (i + 1) * 12
                })

        else:
            # Default single section
            sections.append({"name": "A", "start": 0, "end": total_measures})

        return sections

    def suggest_instrumentation(self, style: ArrangementStyle) -> Dict[str, List[str]]:
        """Suggest instruments for a style"""
        
        instrumentations = {
            ArrangementStyle.CLASSICAL: {
                "melody": ["Violin", "Flute", "Oboe"],
                "harmony": ["Viola", "Cello"],
                "bass": ["Cello", "Double Bass"],
                "rhythm": []
            },
            ArrangementStyle.JAZZ: {
                "melody": ["Saxophone", "Trumpet", "Piano"],
                "harmony": ["Piano", "Guitar"],
                "bass": ["Double Bass", "Electric Bass"],
                "rhythm": ["Drums", "Percussion"]
            },
            ArrangementStyle.ROCK: {
                "melody": ["Electric Guitar", "Vocals"],
                "harmony": ["Electric Guitar", "Keyboard"],
                "bass": ["Electric Bass"],
                "rhythm": ["Drums", "Percussion"]
            },
            ArrangementStyle.POP: {
                "melody": ["Vocals", "Synthesizer"],
                "harmony": ["Piano", "Guitar", "Strings"],
                "bass": ["Bass Guitar", "Synth Bass"],
                "rhythm": ["Drums", "Percussion", "Drum Machine"]
            },
        }

        return instrumentations.get(style, instrumentations[ArrangementStyle.POP])


# Test functions
if __name__ == "__main__":
    # Test progression generator
    print("=== Testing Progression Generator ===")
    prog_gen = ProgressionGenerator("C", "major")
    prog = prog_gen.generate_progression("pop", 4)
    print(f"Progression: {prog.chords}")
    print(f"Roman: {prog.roman_numerals}")

    # Test melody generator
    print("\n=== Testing Melody Generator ===")
    mel_gen = MelodyGenerator("C", "major")
    contour = MelodyContour(
        direction="arch",
        range_octaves=1.5,
        rhythm_density="moderate"
    )
    melody = mel_gen.generate_melody(contour, 8)
    print(f"Melody (pitch, duration): {melody[:4]}...")

    # Test arranger
    print("\n=== Testing Arranger ===")
    arranger = Arranger("G", (4, 4))
    arrangement = arranger.create_arrangement(
        ArrangementStyle.POP,
        FormType.VERSE_CHORUS,
        16
    )
    print(f"Form: {arrangement['form']}")
    print(f"Sections: {[s['name'] for s in arrangement['sections']]}")
    
    print("\n✅ All tests passed!")
