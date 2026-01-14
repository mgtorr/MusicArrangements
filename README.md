# MuseScore LLM Arranger Plugin

A MuseScore plugin that integrates Large Language Models (LLM) to enable natural language control over musical arrangements. Describe the changes you want in plain language, and the plugin will interpret and apply them to your score.

## Features

- **Natural Language Interface**: Describe arrangement changes in plain English/French
- **Multiple LLM Support**: Works with Ollama (local), OpenAI, Anthropic Claude, or custom APIs
- **Smart Score Analysis**: Automatically analyzes your score context for better suggestions
- **Style Transformations**: Apply jazz, rock, classical, latin styles and more
- **Intelligent Harmonization**: Add harmony voices following proper voice-leading principles
- **Orchestration Assistance**: Expand arrangements or reduce to smaller ensembles
- **Dynamic & Articulation Control**: Add crescendos, dynamics, and articulations

## Installation

### Prerequisites

- MuseScore 3.6+ or MuseScore 4.x
- An LLM backend (one of):
  - [Ollama](https://ollama.ai) (recommended for local/free usage)
  - OpenAI API key
  - Anthropic API key
  - Custom LLM API endpoint

### Steps

1. **Download the plugin**
   ```bash
   git clone https://github.com/mgtorr/MusicArrangements.git
   ```

2. **Copy to MuseScore plugins folder**

   - **Windows**: `%HOMEPATH%\Documents\MuseScore3\Plugins\` or `%HOMEPATH%\Documents\MuseScore4\Plugins\`
   - **macOS**: `~/Documents/MuseScore3/Plugins/` or `~/Documents/MuseScore4/Plugins/`
   - **Linux**: `~/Documents/MuseScore3/Plugins/` or `~/Documents/MuseScore4/Plugins/`

   Copy the `src/LLMArrangerPlugin.qml` and associated `.js` files to this directory.

3. **Enable the plugin in MuseScore**
   - Go to `Plugins` → `Plugin Manager`
   - Find "LLM Arranger" and check the box to enable it
   - Restart MuseScore if prompted

4. **Set up your LLM backend**

   **Option A: Ollama (Local, Free)**
   ```bash
   # Install Ollama from https://ollama.ai
   ollama pull llama3  # or another model
   ollama serve  # Start the server (usually runs automatically)
   ```

   **Option B: OpenAI**
   - Get an API key from https://platform.openai.com
   - Configure in plugin settings

   **Option C: Anthropic Claude**
   - Get an API key from https://console.anthropic.com
   - Configure in plugin settings

## Usage

1. **Open a score** in MuseScore

2. **Launch the plugin**: `Plugins` → `LLM Arranger`

3. **Enter your request** in natural language:
   - "Add a violin harmony line a third above the melody"
   - "Transpose the entire piece up a perfect fourth"
   - "Add drums with a rock beat pattern"
   - "Change the style to jazz swing"
   - "Add a crescendo from measure 8 to measure 16"

4. **Click "Apply Changes"** - the plugin will:
   - Send your request to the LLM
   - Parse the response
   - Show you the proposed actions
   - Ask for confirmation before applying

5. **Review and confirm** the changes

## Example Requests

### Arrangement
- "Add a bass line following the chord progression"
- "Harmonize the melody with thirds and sixths"
- "Create a string quartet arrangement"
- "Reduce this to a piano solo"

### Style
- "Apply jazz chord voicings"
- "Make it sound more rock"
- "Add Latin percussion patterns"
- "Make it baroque style with ornaments"

### Dynamics & Expression
- "Add a crescendo in the second phrase"
- "Make measures 1-4 piano and 5-8 forte"
- "Add staccato to the bass line"
- "Add a rallentando at the end"

### Transposition
- "Transpose up a minor third"
- "Move to the key of G major"
- "Transpose for tenor voice range"

## Configuration

### Settings Dialog

Click "Settings" to configure:

| Setting | Description |
|---------|-------------|
| Provider | Select LLM provider (Ollama, OpenAI, Anthropic, Custom) |
| API Endpoint | The URL of the LLM API |
| API Key | Your API key (not needed for local Ollama) |
| Model | The model to use (e.g., llama3, gpt-4, claude-3-sonnet) |

### Default Endpoints

| Provider | Default Endpoint |
|----------|-----------------|
| Ollama | `http://localhost:11434/api/generate` |
| OpenAI | `https://api.openai.com/v1/chat/completions` |
| Anthropic | `https://api.anthropic.com/v1/messages` |

## Project Structure

```
MusicArrangements/
├── src/
│   ├── LLMArrangerPlugin.qml   # Main plugin file
│   ├── ScoreUtils.js           # Score manipulation utilities
│   └── PromptTemplates.js      # LLM prompt templates
├── docs/
│   └── API.md                  # API documentation
├── examples/
│   └── (example scores)
├── package.json
└── README.md
```

## Supported Actions

The plugin can perform these score modifications:

| Action | Description |
|--------|-------------|
| `add_instrument` | Add a new instrument part |
| `remove_instrument` | Remove an existing part |
| `transpose` | Transpose notes by semitones |
| `add_notes` | Add notes to a part |
| `add_dynamics` | Add dynamic markings (pp, p, mp, mf, f, ff) |
| `add_tempo` | Add tempo markings |
| `add_articulation` | Add articulation marks |
| `add_crescendo` | Add hairpin dynamics |
| `harmonize` | Create harmony voices |
| `change_style` | Apply style transformations |

## Limitations

- **Adding instruments**: Due to MuseScore plugin API limitations, adding new instruments may require manual intervention
- **Complex operations**: Some advanced operations may be suggested but need manual implementation
- **LLM accuracy**: Results depend on the LLM's understanding; review all changes before saving

## Troubleshooting

### Plugin doesn't appear
- Ensure the `.qml` file is in the correct plugins folder
- Restart MuseScore after copying files
- Check `Plugins` → `Plugin Manager`

### Connection errors
- For Ollama: Ensure `ollama serve` is running
- Check your API endpoint URL
- Verify your API key is correct

### Poor results
- Try a more capable model (e.g., gpt-4 instead of gpt-3.5)
- Provide more specific requests
- Include context like "in jazz style" or "for piano"

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- MuseScore team for the plugin API
- Ollama, OpenAI, and Anthropic for LLM APIs
- The open-source music technology community
