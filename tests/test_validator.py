import unittest

import _path  # noqa: F401

from validator import CommandValidator, order_commands


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.validator = CommandValidator({
            "measures": 16,
            "staves": 2,
            "time_signature": {"numerator": 4, "denominator": 4},
        })

    def test_invalid_pitch_is_rejected(self):
        result = self.validator.validate_command(
            {"type": "add_note", "pitch": 200, "duration": 480, "measure": 0}
        )
        self.assertFalse(result.valid)

    def test_duration_and_dynamic_are_cleaned(self):
        chord = self.validator.validate_command(
            {"type": "add_chord", "pitches": [60.0, 64, 67], "duration": 500, "measure": 1}
        )
        self.assertTrue(chord.valid)
        self.assertEqual(chord.sanitized_command["duration"], 480)
        self.assertEqual(chord.sanitized_command["pitches"], [60, 64, 67])

        dynamic = self.validator.validate_command({"type": "add_dynamic", "dynamic": "FF", "measure": 2})
        self.assertEqual(dynamic.sanitized_command["dynamic"], "ff")

        tempo = self.validator.validate_command({"type": "add_tempo", "bpm": 500, "measure": 0})
        self.assertTrue(tempo.valid)
        self.assertEqual(tempo.sanitized_command["bpm"], 400)

    def test_overflow_is_a_warning(self):
        _, errors = self.validator.validate_commands([
            {"type": "add_note", "pitch": 60, "duration": 1920, "measure": 0, "tick": 0, "track": 0},
            {"type": "add_note", "pitch": 62, "duration": 480, "measure": 0, "tick": 1920, "track": 0},
        ])
        self.assertEqual(errors, [])
        self.assertTrue(any("past" in warning.lower() or "tick" in warning.lower() for warning in self.validator.last_warnings))

    def test_notes_are_ordered_without_moving_the_tempo(self):
        ordered = order_commands([
            {"type": "add_tempo", "bpm": 90, "measure": 0},
            {"type": "add_note", "pitch": 64, "duration": 480, "measure": 0, "tick": 480, "track": 0},
            {"type": "add_note", "pitch": 60, "duration": 480, "measure": 0, "tick": 0, "track": 0},
        ])
        self.assertEqual(ordered[0]["type"], "add_tempo")
        self.assertEqual([command["pitch"] for command in ordered[1:]], [60, 64])

    def test_bool_is_not_a_pitch(self):
        result = self.validator.validate_command(
            {"type": "add_note", "pitch": True, "duration": 480, "measure": 0}
        )
        self.assertFalse(result.valid)


class PluginContractTests(unittest.TestCase):
    def test_plugin_duration_map_matches_the_server(self):
        from durations import FRACTION_BY_TICKS
        text = (_path.ROOT / "plugin" / "LLMBridge.qml").read_text()
        for ticks, fraction in FRACTION_BY_TICKS.items():
            needle = f'"{ticks}": [{fraction[0]}, {fraction[1]}]'
            self.assertIn(needle, text)
        self.assertIn("function cmdTranspose(command)", text)
        self.assertIn("element.notes[n].pitch = nextPitch", text)
        self.assertNotIn("setDuration(cmd.duration", text)
        self.assertIn("cursor.setDuration(fraction[0], fraction[1])", text)


if __name__ == "__main__":
    unittest.main()
