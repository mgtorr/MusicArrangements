import unittest

import _path  # noqa: F401

from llm_interpreter import parse_llm_payload
from local_interpreter import interpret_locally
from main import usable_api_key


class LocalInterpreterTests(unittest.TestCase):
    def test_readme_chord_request(self):
        result = interpret_locally("Add a C major chord at the beginning")
        self.assertEqual(len(result.commands), 1)
        command = result.commands[0]
        self.assertEqual(command["type"], "add_chord")
        self.assertEqual(command["pitches"], [60, 64, 67])
        self.assertEqual(command["measure"], 0)
        self.assertEqual(command["tick"], 0)
        self.assertEqual(command["duration"], 480)

    def test_transpose_perfect_fifth(self):
        result = interpret_locally("Transpose up a perfect fifth")
        self.assertEqual(result.commands, [{"type": "transpose", "semitones": 7}])

    def test_transpose_down_a_third(self):
        result = interpret_locally("Transpose down a major third")
        self.assertEqual(result.commands[0]["semitones"], -4)

    def test_note_bar_numbers_start_at_one(self):
        result = interpret_locally("Add an F#3 half note in measure 2")
        command = result.commands[0]
        self.assertEqual(command["pitch"], 54)
        self.assertEqual(command["duration"], 960)
        self.assertEqual(command["measure"], 1)

    def test_tempo_and_dynamic(self):
        tempo = interpret_locally("Set the tempo to 96")
        self.assertEqual(tempo.commands[0]["bpm"], 96)
        dynamic = interpret_locally("Add a forte in measure 1")
        self.assertEqual(dynamic.commands[0]["dynamic"], "f")
        self.assertEqual(dynamic.commands[0]["measure"], 0)

    def test_walking_bass_and_drums_phrases(self):
        bass = interpret_locally("Walking bass G C D G for 4 measures")
        self.assertEqual(len(bass.commands), 16)
        self.assertEqual(bass.commands[1]["pitch"], 47)
        drums = interpret_locally("Add a rock drum pattern for 4 measures")
        self.assertEqual(len(drums.commands), 32)
        self.assertTrue(drums.commands[0]["drums"])

    def test_dominant_uses_the_key_signature(self):
        result = interpret_locally("Add the dominant chord", {"key_signature": 1})
        self.assertEqual(result.commands[0]["pitches"], [62, 66, 69])  # D major

    def test_unknown_request_explains_what_works(self):
        result = interpret_locally("make it sound like the ocean at night")
        self.assertEqual(result.commands, [])
        self.assertIn("walking bass", result.notes)

    def test_placeholder_api_key_is_ignored(self):
        self.assertEqual(usable_api_key("YOUR_API_KEY_HERE"), "")
        self.assertEqual(usable_api_key("  "), "")
        self.assertEqual(usable_api_key("sk-real"), "sk-real")


class ModelPayloadTests(unittest.TestCase):
    def test_fenced_json_is_read(self):
        raw = """```json
        {"intent": "Add C", "commands": [{"type": "add_note", "pitch": 60}], "notes": "ok"}
        ```"""
        parsed = parse_llm_payload(raw)
        self.assertEqual(parsed.intent, "Add C")
        self.assertEqual(parsed.commands[0]["pitch"], 60)

    def test_schema_tells_the_model_about_ticks(self):
        from llm_interpreter import COMMAND_SCHEMA
        self.assertIn('"tick"', COMMAND_SCHEMA)
        self.assertIn("measure 3", COMMAND_SCHEMA)


if __name__ == "__main__":
    unittest.main()
