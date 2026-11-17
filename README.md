# MuseScore LLM Bridge

Write musical changes into an open MuseScore score. Type the change in the score plugin or in the desk at `http://localhost:8766`.

```
┌─────────────────┐     HTTP poll      ┌──────────────────┐
│   MuseScore     │◀──────────────────▶│  Python server   │
│   QML plugin    │   notes, chords,   │  theory or LLM   │
└─────────────────┘   tempo, drums     └──────────────────┘
```

With an API key, Claude, Gemini, or OpenAI reads the sentence. Without one, a local theory engine handles the requests below.

## Install

```bash
pip install -r requirements.txt
cp server/config.example.json server/config.json   # optional, for a model key
```

Copy `plugin/LLMBridge.qml` into the MuseScore 4 plugins folder:

- Windows: `%HOMEPATH%\Documents\MuseScore4\Plugins\`
- macOS and Linux: `~/Documents/MuseScore4/Plugins/`

Enable it in Plugins → Plugin Manager.

A model key is optional. Set `LLM_API_KEY` and `LLM_PROVIDER` (`claude`, `gemini`, or `openai`), or put them in `server/config.json`. `server/config.json` is gitignored. The placeholder in the example file is not sent to a provider.

## Use

```bash
cd server
python main.py --headless
```

Open `http://localhost:8766`. In MuseScore, open a score, run Plugins → LLM Bridge, and press Connect. The desk shows the score title, time signature, and key once the plugin has reported them.

Requests that work with no API key:

- `Add a C major chord at the beginning`
- `Add an F#3 half note in measure 2`
- `Add a forte in measure 1`
- `Set the tempo to 96`
- `Transpose up a perfect fifth`
- `Walking bass G C D G for 4 measures`
- `Rock drums for 4 measures` (also jazz, pop, latin, metal)

Bar numbers in those sentences start at 1. The same box accepts a freer sentence when a model is configured. If the model returns nothing usable, the local engine tries the sentence too.

The plugin can send the same sentences. Its log shows the intent, and the notes land in the score as one undo step.

`python main.py` without `--headless` keeps a terminal prompt (`/bass`, `/drums`, `/info`, `/ping`, `/quit`) and still serves the desk. Typing at the prompt does not freeze the plugin connection.

## What gets written

Notes are placed by tick inside the bar. A quarter note is 480 ticks, so 4/4 beats are 0, 480, 960, and 1440. The plugin converts those ticks to a real note length (`1/4`, not 480 whole notes).

Walking bass plays one chord tone per beat and steps chromatically into the next chord. `Gmaj` is major; `Gm` is minor. Drum hits that share a beat are written together, and each bar is filled in time. Patterns are in 4/4.

Transpose moves every note in the score, including a drum staff. Undo if the kit should stay put.

| Command | Role |
| --- | --- |
| `add_note` | One pitch, duration, measure, tick, track |
| `add_chord` | Several pitches at one tick |
| `add_rest` | A rest, used to reach a later beat |
| `add_dynamic` | `pp` through `ff`, plus `sfz` |
| `add_tempo` | BPM at a bar |
| `add_text` | Staff or system text |
| `transpose` | Semitones, positive or negative |

MIDI 60 is C4. Track 0 is the first voice of the first staff.

## Tests

```bash
python -m unittest discover -s tests
```

## Layout

```
plugin/LLMBridge.qml     MuseScore dialog
server/main.py           Startup, CLI, request handling
server/bridge_server.py  HTTP desk, poll, and results
server/console.html      Desk page
server/local_interpreter.py
server/music_logic.py
server/validator.py
server/llm_interpreter.py
server/durations.py      Tick values shared with the plugin
```

## Troubleshooting

The desk says the plugin is not connected: start `python main.py`, then press Connect in the plugin. The server listens on port 8766.

A request stays queued: the plugin dialog has to stay open. It picks up commands several times a second.

The model is not used: `LLM_API_KEY` is empty or still the example placeholder. The local engine answers instead.

A bar looks too full: the desk lists a warning when the written ticks run past the time signature. Drum patterns assume 4/4.
