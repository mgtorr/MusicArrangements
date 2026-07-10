# MuseScore LLM Bridge - Composition Assistant

AI-powered music arrangement and composition for MuseScore using the "Bridge" architecture with advanced composition assistant capabilities.

## Features

### 🎵 Natural Language Composition
- **AI-Powered Understanding**: Describe what you want in plain English
- **Music Theory Intelligence**: LLM understands harmony, voice leading, counterpoint
- **Style-Specific Composition**: Jazz, Classical, Pop, Rock, Blues, Folk

### 🎼 Advanced Composition Tools
- **Melody Generation**: Create melodic lines with specified contours and rhythms
- **Chord Progressions**: Generate progressions in various styles (I-V-vi-IV, ii-V-I, 12-bar blues)
- **Harmonization**: Add harmonies to melodies (thirds, sixths, full chords)
- **Voice Leading**: Smooth voice transitions following classical rules
- **Full Arrangements**: Complete multi-section arrangements with form structure

### 🎹 Built-in Music Logic
- **Walking Bass Lines**: Automatic bass patterns from chord symbols
- **Drum Patterns**: Rock, jazz, pop, Latin, metal drum grooves
- **Form Structure**: Verse-chorus, ABA, AABA, Rondo, Sonata
- **Instrumentation Suggestions**: Context-aware instrument recommendations

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

### 3. Compose with Natural Language

In the server terminal, describe what you want:

```
>>> Compose a jazz melody in G major with an arch contour
>>> Add a ii-V-I progression in C major
>>> Create a pop verse-chorus arrangement in 16 measures
>>> Harmonize the melody in thirds
>>> Add a walking bass line over these chords: Cmaj Amin Fmaj G7
>>> Generate rock drums for 8 measures
```

### 4. Use Built-in Composition Tools

Interactive commands for specific tasks:

```
>>> /melody
Key (e.g., C, G, Dm): G
Contour (ascending/descending/arch/static): arch
Number of measures: 8
Rhythm density (sparse/moderate/dense): moderate

>>> /progression
Key (e.g., C, G, Am): C  
Style (pop/jazz/classical/blues/folk): jazz
Number of measures: 8

>>> /arrange
Key (e.g., C, G): G
Style (pop/jazz/rock/classical/blues): pop
Form (verse_chorus/ABA/AABA): verse_chorus
Total measures: 16

>>> /bass
Chords (e.g., G C D G): G Am F G
Measures: 4

>>> /drums
Style (rock/jazz/pop/latin/metal): jazz
Measures: 8
```

## Example Composition Workflows

### Create a Complete Song

```
>>> /arrange
Key: G
Style: pop
Form: verse_chorus  
Total measures: 16
# Creates verse-chorus structure with progressions

>>> Compose a catchy melody over the chords in measures 0-7
# LLM generates melodic line

>>> Add harmonization in sixths to the melody
# Adds harmony voice

>>> /drums
Style: pop
Measures: 16
# Adds drum pattern

>>> Add a simple bass line following the chord roots
# LLM generates supportive bass
```

### Jazz Composition

```
>>> /progression
Key: Dm
Style: jazz
Number of measures: 8
# Generates ii-V-I style progression with 7th chords

>>> Create a jazz melody with moderate syncopation over these chords
# LLM generates bebop-style melody

>>> /bass
Chords: Dm7 G7 Cmaj7 A7 Dm7 G7 Cmaj7 Cmaj7
Measures: 8
# Walking bass pattern

>>> /drums  
Style: jazz
Measures: 8
# Swing drum pattern with ride cymbal
```

### Classical Arrangement

```
>>> Create a classical ABA form arrangement in C major, 24 measures
# Full classical structure

>>> Compose a lyrical melody in the style of Mozart
# Elegant classical melody

>>> Add classical string harmonization with proper voice leading
# 4-part harmony following voice leading rules
```

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
