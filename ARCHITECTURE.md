# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                            │
│                                                                     │
│  Natural Language:  "Create a jazz melody with arch contour"       │
│  CLI Commands:      /melody, /progression, /arrange                │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PYTHON SERVER (The Brain)                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    LLM INTERPRETER                            │ │
│  │                                                               │ │
│  │  ┌──────────────┐      ┌─────────────────┐                  │ │
│  │  │ Task Detector│─────▶│ Prompt Selector │                  │ │
│  │  │ (keywords)   │      │ (specialized)   │                  │ │
│  │  └──────────────┘      └─────────────────┘                  │ │
│  │         │                       │                            │ │
│  │         ▼                       ▼                            │ │
│  │  ┌───────────────────────────────────────┐                  │ │
│  │  │   COMPOSITION PROMPTS                 │                  │ │
│  │  │   • Melody Prompts                    │                  │ │
│  │  │   • Harmony Prompts                   │                  │ │
│  │  │   • Style-Specific (jazz, classical)  │                  │ │
│  │  │   • Music Theory Context              │                  │ │
│  │  └───────────────────────────────────────┘                  │ │
│  └────────────────────────┬───────────────────────────────────────┘ │
│                           ▼                                         │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │              LLM PROVIDER (Claude/Gemini/OpenAI)              │ │
│  │              Returns JSON with commands                       │ │
│  └────────────────────────┬───────────────────────────────────────┘ │
│                           ▼                                         │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                COMPOSITION ASSISTANT                          │ │
│  │                                                               │ │
│  │  ┌──────────────────┐  ┌──────────────────┐                 │ │
│  │  │ Progression Gen  │  │ Melody Generator │                 │ │
│  │  │ • Pop            │  │ • Contours       │                 │ │
│  │  │ • Jazz           │  │ • Rhythm density │                 │ │
│  │  │ • Classical      │  │ • Scale-aware    │                 │ │
│  │  └──────────────────┘  └──────────────────┘                 │ │
│  │                                                               │ │
│  │  ┌──────────────────┐  ┌──────────────────┐                 │ │
│  │  │ Harmonizer       │  │ Arranger         │                 │ │
│  │  │ • Voice leading  │  │ • Form structure │                 │ │
│  │  │ • Thirds/Sixths  │  │ • Multi-section  │                 │ │
│  │  └──────────────────┘  └──────────────────┘                 │ │
│  └────────────────────────┬──────────────────────────────────────┘ │
│                           ▼                                         │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    MUSIC LOGIC (Music21)                      │ │
│  │  • Walking Bass Generator                                     │ │
│  │  • Drum Pattern Generator                                     │ │
│  │  • Scale/Chord Utilities                                      │ │
│  └────────────────────────┬──────────────────────────────────────┘ │
│                           ▼                                         │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                     COMMAND VALIDATOR                         │ │
│  │  • Check pitch ranges (0-127)                                 │ │
│  │  • Validate measure numbers                                   │ │
│  │  • Verify durations                                           │ │
│  └────────────────────────┬──────────────────────────────────────┘ │
│                           ▼                                         │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                   BRIDGE SERVER (HTTP)                        │ │
│  │  • Queue commands                                             │ │
│  │  • Manage connection state                                    │ │
│  │  • Track score info                                           │ │
│  └────────────────────────┬──────────────────────────────────────┘ │
└────────────────────────────┼──────────────────────────────────────┘
                             │ HTTP (localhost:8766)
                             │ • /ping, /poll
                             │ • /score_info, /results
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    MUSESCORE PLUGIN (The Ear)                       │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                     LLMBridge.qml                             │ │
│  │                                                               │ │
│  │  • Poll server every 1s                                       │ │
│  │  • Receive command batches                                    │ │
│  │  • Execute atomic commands:                                   │ │
│  │    - add_note                                                 │ │
│  │    - add_chord                                                │ │
│  │    - add_rest                                                 │ │
│  │    - add_dynamic                                              │ │
│  │    - add_tempo                                                │ │
│  │    - add_text                                                 │ │
│  │    - transpose                                                │ │
│  │  • Send score info back                                       │ │
│  └────────────────────────┬──────────────────────────────────────┘ │
└────────────────────────────┼──────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       MUSESCORE APPLICATION                         │
│  • Render notation                                                  │
│  • Playback audio                                                   │
│  • Export (PDF, MIDI, MusicXML)                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Example: "Create a jazz melody"

```
1. USER INPUT
   "Create a jazz melody in G major with an arch contour"
   
2. TASK DETECTION
   Keywords: "melody", "jazz" 
   → Route to: Melody + Style prompts
   
3. PROMPT CONSTRUCTION
   Combine:
   - MELODY_COMPOSITION_PROMPT
   - JAZZ_STYLE_PROMPT
   - Music theory context
   - Current score state
   
4. LLM PROCESSING
   Claude/Gemini/OpenAI generates:
   {
     "intent": "Compose jazz melody with arch contour",
     "commands": [
       {"type": "add_note", "pitch": 67, "duration": 480, "measure": 0, "track": 0},
       {"type": "add_note", "pitch": 69, "duration": 240, "measure": 0, "track": 0},
       ...
     ],
     "notes": "Using G major scale with jazz chromatic passing tones"
   }
   
5. VALIDATION
   - Pitch 67 (G4) ✓ within range
   - Duration 480 ✓ valid
   - Measure 0 ✓ exists
   - Track 0 ✓ exists
   
6. COMMAND QUEUING
   Commands added to pending queue
   
7. PLUGIN POLLING
   Plugin polls /poll endpoint
   Receives command batch
   
8. EXECUTION
   For each command:
     - cursor.setDuration(480, 1)
     - cursor.addNote(67)
   
9. RESULT
   Melody appears in MuseScore
   Score updated with new notes
```

## Module Responsibilities

### `llm_interpreter.py`
- **Purpose**: Translate natural language to commands
- **Input**: User text + score context
- **Output**: Structured commands (JSON)
- **Key Features**:
  - Auto-detect task type
  - Select appropriate prompt
  - Handle multiple LLM providers

### `composition_prompts.py`
- **Purpose**: Specialized prompts for music tasks
- **Contains**:
  - Task prompts (melody, harmony, rhythm)
  - Style prompts (jazz, classical, pop)
  - Music theory context
- **Output**: Formatted prompt text

### `composition_assistant.py`
- **Purpose**: Algorithmic composition logic
- **Components**:
  - `ProgressionGenerator`: Chord progressions
  - `MelodyGenerator`: Melodic lines
  - `Harmonizer`: Voice-led harmonies
  - `Arranger`: Full arrangements
- **Uses**: Music21 for theory calculations

### `music_logic.py`
- **Purpose**: Pattern generators
- **Generators**:
  - Walking bass lines
  - Drum patterns (rock, jazz, etc.)
  - Scale/chord utilities
- **Uses**: Music21 + custom algorithms

### `bridge_server.py`
- **Purpose**: HTTP server for plugin communication
- **Endpoints**:
  - `/ping`: Connection check
  - `/poll`: Get pending commands
  - `/score_info`: Receive score state
  - `/results`: Execution feedback
- **State**: Manages connection, queue, score info

### `validator.py`
- **Purpose**: Validate commands before sending
- **Checks**:
  - Pitch ranges (0-127)
  - Duration values
  - Measure bounds
  - Track existence

### `main.py`
- **Purpose**: Orchestrate all components
- **Features**:
  - CLI interface
  - Action methods for composition features
  - Configuration management
  - Error handling

## Communication Protocol

### Plugin → Server

```
POST /score_info
{
  "title": "My Composition",
  "measures": 32,
  "staves": 2,
  "time_signature": {"numerator": 4, "denominator": 4},
  "key_signature": 0,
  "parts": [{"name": "Piano"}]
}
```

### Server → Plugin

```
GET /poll
Response:
{
  "commands": [
    {"type": "add_note", "pitch": 60, "duration": 480, "measure": 0, "track": 0},
    {"type": "add_chord", "pitches": [60, 64, 67], "duration": 960, "measure": 1, "track": 0}
  ]
}
```

### Plugin → Server (Results)

```
POST /results
{
  "executed": 156,
  "success": true
}
```

## Configuration Flow

```
1. Load config.json
   ├─ provider: "claude"
   ├─ api_key: "sk-ant-..."
   └─ model: "claude-sonnet-4-20250514"

2. Initialize LLM Interpreter
   └─ Set provider with credentials

3. Start HTTP Server
   └─ Listen on localhost:8766

4. Wait for plugin connection
   └─ Plugin sends /ping

5. Ready for commands
   └─ User input → LLM → Commands → MuseScore
```

## Extension Points

### Add New Composition Feature

1. Create generator in `composition_assistant.py`
2. Add specialized prompt in `composition_prompts.py`
3. Add CLI command in `main.py`
4. Add action method to process requests
5. Update documentation

### Add New Style

1. Add style to `STYLE_CHARACTERISTICS` in `composition_prompts.py`
2. Update `ProgressionGenerator.COMMON_PROGRESSIONS`
3. Test with `/progression` command

### Add New LLM Provider

1. Implement provider class in `llm_interpreter.py`
2. Follow `LLMProvider` abstract interface
3. Add to `LLMInterpreter.set_provider()`
4. Update `config.example.json`

## Performance Characteristics

### Latency
- LLM Request: 2-10 seconds
- Command Validation: <10ms
- HTTP Communication: <50ms
- MuseScore Execution: 10-100ms per command

### Throughput
- Commands per request: 1-100+
- Requests per minute: Limited by LLM rate limits
- Score updates: Real-time (1s polling)

### Memory
- Server: ~50-100MB
- Plugin: Minimal (QML)
- Score data: Cached in server

---

This architecture balances:
- **AI intelligence** (LLM understanding)
- **Music theory** (composition algorithms)
- **Real-time execution** (MuseScore plugin)
- **Extensibility** (modular design)
