# MuseScore LLM Bridge

AI-powered music arrangement for MuseScore using the "Bridge" architecture.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   MuseScore     │────▶│  Python Server   │────▶│      LLM        │
│   QML Plugin    │◀────│   (Middleware)   │◀────│ (Claude/Gemini) │
│   "The Ear"     │     │   "The Brain"    │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
     WebSocket              Music21                   API
```

### Components

1. **The Ear** (MuseScore Plugin)
   - QML plugin that listens for commands via WebSocket
   - Executes atomic commands on the score
   - Reports score state back to server

2. **The Brain** (Python Middleware)
   - Receives natural language requests
   - Uses LLM to interpret intent
   - Uses Music21 for musical calculations
   - Validates commands before sending
   - Sends atomic commands to plugin

3. **The Translator** (LLM)
   - Interprets natural language requests
   - Generates structured commands
   - Understands musical concepts

## Installation

### 1. Install Python Server

```bash
cd MusicArrangements
pip install -r requirements.txt

# Copy and edit config
cp server/config.example.json server/config.json
# Edit config.json with your API key
```

### 2. Install MuseScore Plugin

Copy `plugin/LLMBridge.qml` to your MuseScore plugins folder:

- **Windows**: `%HOMEPATH%\Documents\MuseScore4\Plugins\`
- **macOS**: `~/Documents/MuseScore4/Plugins/`
- **Linux**: `~/Documents/MuseScore4/Plugins/`

Enable in MuseScore: Plugins → Plugin Manager → LLM Bridge

### 3. Configure API Key

Set environment variable:
```bash
export LLM_API_KEY="your-api-key"
export LLM_PROVIDER="claude"  # or "gemini" or "openai"
```

Or edit `server/config.json`:
```json
{
    "provider": "claude",
    "api_key": "sk-ant-...",
    "model": "claude-sonnet-4-20250514"
}
```

## Usage

### 1. Start the Server

```bash
cd MusicArrangements/server
python main.py
```

### 2. Connect MuseScore

1. Open MuseScore
2. Open a score
3. Launch plugin: Plugins → LLM Bridge
4. Click "Connect to Server"

### 3. Send Commands

In the server terminal:
```
>>> Add a C major chord at the beginning
>>> Add walking bass in G major
>>> Transpose up a perfect fifth
>>> Add rock drum pattern for 4 measures
```

Or use built-in music logic:
```
>>> /bass
Chords (e.g., G C D G): G C D G
Measures: 4

>>> /drums
Style (rock/jazz/pop/latin/metal): jazz
Measures: 8
```

## Atomic Commands

The system uses these atomic commands:

| Command | Description | Parameters |
|---------|-------------|------------|
| `add_note` | Add single note | pitch, duration, measure, track |
| `add_chord` | Add chord | pitches[], duration, measure, track |
| `add_rest` | Add rest | duration, measure, track |
| `add_dynamic` | Add dynamic | dynamic (pp/p/mp/mf/f/ff), measure |
| `add_tempo` | Add tempo | bpm, measure, text |
| `add_text` | Add text | text, measure, textType |
| `transpose` | Transpose | semitones |

## MIDI Pitch Reference

```
C4 (middle C) = 60
D4 = 62, E4 = 64, F4 = 65, G4 = 67, A4 = 69, B4 = 71
C5 = 72, C3 = 48, C2 = 36 (bass)
```

## Duration Reference (ticks)

```
Whole = 1920
Half = 960
Quarter = 480
Eighth = 240
16th = 120
```

## Supported LLM Providers

| Provider | Models | API Key Format |
|----------|--------|----------------|
| Claude | claude-sonnet-4-20250514, claude-3-5-sonnet | sk-ant-... |
| Gemini | gemini-2.0-flash, gemini-1.5-pro | AIza... |
| OpenAI | gpt-4o, gpt-4-turbo | sk-... |

## Project Structure

```
MusicArrangements/
├── plugin/
│   └── LLMBridge.qml      # MuseScore plugin
├── server/
│   ├── main.py            # Main server entry point
│   ├── bridge_server.py   # WebSocket bridge
│   ├── llm_interpreter.py # LLM integration
│   ├── music_logic.py     # Music21 calculations
│   ├── validator.py       # Command validation
│   └── config.json        # Configuration
├── schemas/               # Command schemas
├── requirements.txt
└── README.md
```

## Troubleshooting

### Plugin shows "Disconnected"
- Ensure Python server is running (`python main.py`)
- Check that port 8766 is not blocked

### LLM errors
- Verify API key is correct
- Check provider name matches key type
- Try a different model

### Commands not executing
- Check MuseScore console for errors
- Verify score is open
- Check command validation errors in server output

## Development

### Adding New Commands

1. Add command handler in `plugin/LLMBridge.qml`
2. Add command schema in `server/llm_interpreter.py`
3. Add validation in `server/validator.py`

### Adding Music Logic

Add functions to `server/music_logic.py` using Music21.

## License

MIT License
