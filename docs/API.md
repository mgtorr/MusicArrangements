# LLM Arranger Plugin - API Documentation

This document describes the internal API and action format used by the LLM Arranger Plugin.

## Action Format

All actions follow this JSON structure:

```json
{
    "type": "action_type",
    "params": {
        // action-specific parameters
    },
    "description": "Optional human-readable description"
}
```

## Available Actions

### add_instrument

Add a new instrument part to the score.

```json
{
    "type": "add_instrument",
    "params": {
        "name": "Violin",
        "family": "strings",
        "clef": "treble"
    }
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | string | Yes | Instrument name |
| family | string | No | Instrument family (strings, woodwinds, brass, percussion, keyboards) |
| clef | string | No | Default clef (treble, bass, alto, tenor) |

**Note**: Due to MuseScore plugin API limitations, this action may only suggest the instrument to add.

---

### remove_instrument

Remove an instrument part from the score.

```json
{
    "type": "remove_instrument",
    "params": {
        "partIndex": 2,
        "name": "Flute"
    }
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| partIndex | number | No* | Index of the part (0-based) |
| name | string | No* | Name of the instrument |

*Either partIndex or name is required.

---

### transpose

Transpose notes in the score.

```json
{
    "type": "transpose",
    "params": {
        "semitones": 5,
        "selection": "all",
        "partIndex": 0,
        "startMeasure": 1,
        "endMeasure": 16
    }
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| semitones | number | Yes | Number of semitones (+/-) |
| selection | string | No | "all", "part", or "measures" (default: "all") |
| partIndex | number | No | Part to transpose (if selection is "part") |
| startMeasure | number | No | Start measure (if selection is "measures") |
| endMeasure | number | No | End measure (if selection is "measures") |

---

### add_notes

Add notes to a specific location in the score.

```json
{
    "type": "add_notes",
    "params": {
        "partIndex": 0,
        "measure": 5,
        "beat": 1,
        "pitches": [60, 64, 67],
        "duration": "quarter"
    }
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| partIndex | number | Yes | Part index (0-based) |
| measure | number | Yes | Measure number (1-based) |
| beat | number | Yes | Beat position in measure |
| pitches | number[] | Yes | Array of MIDI pitch values |
| duration | string | Yes | Note duration (whole, half, quarter, eighth, sixteenth) |

---

### add_dynamics

Add a dynamic marking to the score.

```json
{
    "type": "add_dynamics",
    "params": {
        "type": "mf",
        "measure": 1,
        "partIndex": 0
    }
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| type | string | Yes | Dynamic type: pp, p, mp, mf, f, ff, sfz, fp |
| measure | number | Yes | Measure number (1-based) |
| partIndex | number | No | Part index (default: 0) |

---

### add_tempo

Add a tempo marking to the score.

```json
{
    "type": "add_tempo",
    "params": {
        "bpm": 120,
        "measure": 1,
        "text": "Allegro"
    }
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| bpm | number | Yes | Beats per minute |
| measure | number | No | Measure number (default: 1) |
| text | string | No | Tempo text (e.g., "Allegro", "Andante") |

---

### add_articulation

Add articulation markings to notes.

```json
{
    "type": "add_articulation",
    "params": {
        "type": "staccato",
        "partIndex": 0,
        "startMeasure": 1,
        "endMeasure": 8
    }
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| type | string | Yes | Articulation type (see below) |
| partIndex | number | No | Part index (default: 0) |
| startMeasure | number | Yes | Start measure |
| endMeasure | number | Yes | End measure |

**Articulation types**: staccato, accent, tenuto, marcato, fermata, staccatissimo, portato

---

### add_crescendo

Add hairpin dynamics (crescendo/decrescendo).

```json
{
    "type": "add_crescendo",
    "params": {
        "type": "crescendo",
        "startMeasure": 5,
        "endMeasure": 12,
        "partIndex": 0
    }
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| type | string | Yes | "crescendo" or "decrescendo" |
| startMeasure | number | Yes | Start measure |
| endMeasure | number | Yes | End measure |
| partIndex | number | No | Part index (default: 0) |

---

### harmonize

Create harmony voices from an existing part.

```json
{
    "type": "harmonize",
    "params": {
        "sourcePart": 0,
        "intervals": [4, 7],
        "newPartName": "Harmony"
    }
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| sourcePart | number | Yes | Index of the source part |
| intervals | number[] | Yes | Semitone intervals for harmony voices |
| newPartName | string | No | Name for the new harmony part |

---

### copy_pattern

Copy and transform a musical pattern.

```json
{
    "type": "copy_pattern",
    "params": {
        "sourcePart": 0,
        "targetPart": 1,
        "transformation": "octave_down"
    }
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| sourcePart | number | Yes | Source part index |
| targetPart | number | Yes | Target part index |
| transformation | string | No | Transformation to apply |

**Transformations**: octave_up, octave_down, invert, retrograde, augment, diminish

---

### change_style

Apply style-specific transformations.

```json
{
    "type": "change_style",
    "params": {
        "style": "jazz",
        "parameters": {
            "swing": true,
            "extensions": true
        }
    }
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| style | string | Yes | Target style name |
| parameters | object | No | Style-specific options |

**Supported styles**: jazz, rock, classical, baroque, romantic, latin, pop, electronic

---

## LLM Response Format

The LLM should respond with this JSON structure:

```json
{
    "understanding": "Brief description of what was understood",
    "actions": [
        {
            "type": "action_type",
            "params": { ... },
            "description": "What this action does"
        }
    ],
    "explanation": "Musical rationale for the changes",
    "warnings": ["Any potential issues or limitations"]
}
```

## Score Information Format

The plugin provides score context to the LLM:

```json
{
    "title": "Score Title",
    "composer": "Composer Name",
    "parts": 4,
    "measures": 32,
    "instruments": ["Piano", "Violin", "Cello", "Flute"],
    "keySignature": "G Major",
    "timeSignature": "4/4",
    "tempo": 120
}
```

## Error Handling

Actions may fail and return descriptive error messages. Common errors:

- `"No score open"` - No score is currently loaded
- `"Invalid part index"` - Part index out of range
- `"Invalid measure"` - Measure number out of range
- `"Action not supported"` - Action type not implemented
- `"API error"` - LLM API communication failed
