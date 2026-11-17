import unittest

import _path  # noqa: F401

from durations import FRACTION_BY_TICKS, nearest_duration, ticks_to_fraction
from music_logic import MusicGenerator, describe_command, parse_chord_symbol


class DurationTests(unittest.TestCase):
    def test_quarter_is_one_over_four(self):
        self.assertEqual(ticks_to_fraction(480), (1, 4))
        self.assertEqual(ticks_to_fraction(1920), (1, 1))
        self.assertEqual(ticks_to_fraction(320), (1, 6))

    def test_nearest_duration_snaps_toward_a_real_value(self):
        self.assertEqual(nearest_duration(500), 480)
        self.assertEqual(nearest_duration(240), 240)


class ChordSymbolTests(unittest.TestCase):
    def test_major_spelling_is_not_minor(self):
        self.assertEqual(parse_chord_symbol("Gmaj"), ("G", "major"))
        self.assertEqual(parse_chord_symbol("G"), ("G", "major"))
        self.assertEqual(parse_chord_symbol("C#"), ("C#", "major"))

    def test_minor_and_seventh_spellings(self):
        self.assertEqual(parse_chord_symbol("Gm"), ("G", "minor"))
        self.assertEqual(parse_chord_symbol("Gmin"), ("G", "minor"))
        self.assertEqual(parse_chord_symbol("Am7"), ("A", "min7"))
        self.assertEqual(parse_chord_symbol("Gmaj7"), ("G", "maj7"))
        self.assertEqual(parse_chord_symbol("D7"), ("D", "dom7"))
        self.assertEqual(parse_chord_symbol("Bb"), ("Bb", "major"))
        self.assertEqual(parse_chord_symbol("F#dim"), ("F#", "dim"))

    def test_unknown_quality_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_chord_symbol("H7")


class PatternTests(unittest.TestCase):
    def test_walking_bass_uses_major_third_for_gmaj(self):
        commands = MusicGenerator("G", (4, 4)).walking_bass_line(["Gmaj", "C", "D", "G"], measures=1)
        self.assertEqual(len(commands), 4)
        self.assertEqual(commands[0]["pitch"], 43)  # G2
        self.assertEqual(commands[1]["pitch"], 47)  # B2, not Bb
        self.assertEqual([command["tick"] for command in commands], [0, 480, 960, 1440])
        self.assertEqual(sum(command["duration"] for command in commands), 1920)

    def test_walking_bass_minor(self):
        commands = MusicGenerator("G", (4, 4)).walking_bass_line(["Gm"], measures=1)
        self.assertEqual(commands[1]["pitch"], 46)  # Bb2

    def test_rock_drums_share_beats_and_fill_the_bar(self):
        commands = MusicGenerator().drum_pattern("rock", measures=1)
        self.assertEqual(len(commands), 8)
        self.assertEqual(commands[0]["type"], "add_chord")
        self.assertEqual(commands[0]["tick"], 0)
        self.assertIn(36, commands[0]["pitches"])
        self.assertIn(42, commands[0]["pitches"])
        self.assertEqual(sum(command["duration"] for command in commands), 1920)
        ticks = [command["tick"] for command in commands]
        self.assertEqual(ticks, sorted(ticks))
        self.assertIn("kick", describe_command(commands[0]))

    def test_jazz_drums_fill_the_bar(self):
        commands = MusicGenerator().drum_pattern("jazz", measures=2)
        first_bar = [command for command in commands if command["measure"] == 0]
        self.assertEqual(sum(command["duration"] for command in first_bar), 1920)
        self.assertTrue(all(command["duration"] in FRACTION_BY_TICKS for command in commands))


if __name__ == "__main__":
    unittest.main()
