# Muse AI Sidecar

AI-powered music arrangement desktop application for MuseScore, built with Tauri and React.

## Architecture

```
┌─────────────────┐     ┌──────────────────────────┐     ┌─────────────────┐
│   MuseScore     │────▶│   Muse AI Sidecar        │────▶│      LLM        │
│   QML Plugin    │◀────│   (Tauri/React Desktop)  │◀────│ (Claude/Gemini) │
│   "The Ear"     │     │   "The Brain"            │     │                 │
└─────────────────┘     └──────────────────────────┘     └─────────────────┘
     HTTP Polling              Rust Backend                    API
```

### Components

1. **The Ear** (MuseScore Plugin)
   - QML plugin that polls for commands via HTTP
   - Executes atomic commands on the score
   - Reports score state back to sidecar

2. **The Brain** (Tauri Desktop App)
   - Modern React UI for interaction
   - Rust backend for HTTP bridge server
   - LLM integration (Claude, Gemini, OpenAI)
   - Music generation and command validation

3. **The Translator** (LLM)
   - Interprets natural language requests
   - Generates structured commands
   - Understands musical concepts

## Features

- Natural language to music commands
- Walking bass line generation
- Drum pattern generation (rock, jazz, pop, latin, metal)
- Support for multiple LLM providers
- Real-time score information display
- Cross-platform desktop application

## Installation

### Prerequisites

- [Node.js](https://nodejs.org/) 18+
- [Rust](https://rustup.rs/) 1.70+
- [MuseScore 4](https://musescore.org/)

### 1. Clone and Install

```bash
git clone <repository>
cd MusicArrangements

# Install dependencies
npm install
```

### 2. Install MuseScore Plugin

Copy `plugin/LLMBridge.qml` to your MuseScore plugins folder:

- **Windows**: `%HOMEPATH%\Documents\MuseScore4\Plugins\`
- **macOS**: `~/Documents/MuseScore4/Plugins/`
- **Linux**: `~/Documents/MuseScore4/Plugins/`

Enable in MuseScore: Plugins → Plugin Manager → LLM Bridge

### 3. Configure API Key

Launch the app and go to Settings to configure your LLM provider and API key.

Or set environment variables:
```bash
export LLM_API_KEY="your-api-key"
export LLM_PROVIDER="claude"  # or "gemini" or "openai"
```

## Development

### Run in Development Mode

```bash
npm run tauri:dev
```

### Build for Production

```bash
npm run tauri:build
```

## Usage

### 1. Start the Application

Launch Muse AI Sidecar and click "Start Server" to begin listening for MuseScore connections.

### 2. Connect MuseScore

1. Open MuseScore
2. Open a score
3. Launch plugin: Plugins → LLM Bridge
4. Click "Connect to Server"

### 3. Send Commands

Type natural language requests in the chat panel:
```
Add a C major chord at the beginning
Add walking bass in G major for 4 measures
Transpose up a perfect fifth
Add rock drum pattern for 4 measures
```

Or use slash commands:
```
/bass C G Am F 4    (chords followed by measures)
/drums rock 4       (style followed by measures)
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
muse-ai-sidecar/
├── src/                    # React frontend
│   ├── components/         # UI components
│   ├── lib/               # State and commands
│   └── styles/            # CSS/Tailwind
├── src-tauri/             # Rust backend
│   └── src/
│       ├── bridge.rs      # HTTP bridge server
│       ├── llm.rs         # LLM interpreters
│       ├── music.rs       # Music generation
│       ├── validator.rs   # Command validation
│       └── commands.rs    # Tauri commands
├── plugin/
│   └── LLMBridge.qml      # MuseScore plugin
├── package.json
└── README.md
```

## Troubleshooting

### Plugin shows "Disconnected"
- Ensure Muse AI Sidecar is running with server started
- Check that port 8766 is not blocked

### LLM errors
- Verify API key is correct in Settings
- Check provider name matches key type
- Try a different model

### Commands not executing
- Check MuseScore console for errors
- Verify score is open in MuseScore
- Check log panel for validation errors

## Tech Stack

- **Frontend**: React, TypeScript, Tailwind CSS
- **Backend**: Rust, Tauri 2.0
- **Build**: Vite
- **State**: Zustand
- **LLM**: Claude, Gemini, OpenAI APIs

## License

MIT License
