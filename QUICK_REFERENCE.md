# MuseScore Composition Assistant - Quick Reference

## 🎵 Natural Language Commands

### Melody
```
>>> Compose a [style] melody in [key] with [contour] motion
>>> Add a melodic line spanning [range] over [measures] measures
>>> Create a [mood] melody for the [section]
```

### Harmony & Chords
```
>>> Add a [progression type] in [key]
>>> Create [style] chord progression for [measures] measures
>>> Harmonize the melody in [interval]
>>> Add [chord type] chords following the bass
```

### Bass Lines
```
>>> Add a walking bass line over [chords]
>>> Create [style] bass pattern for [measures] measures
>>> Generate simple bass following chord roots
```

### Rhythm & Drums
```
>>> Add [style] drum pattern for [measures] measures
>>> Create a [feel] groove
>>> Generate percussion with [intensity]
```

### Full Arrangements
```
>>> Create a [style] arrangement in [form] for [measures] measures
>>> Build a [structure] composition in [key]
>>> Generate [section] in [style]
```

## 🎹 Interactive Commands

| Command | Purpose | Prompts |
|---------|---------|---------|
| `/melody` | Generate melody | Key, Contour, Measures, Density |
| `/progression` | Chord progression | Key, Style, Measures |
| `/bass` | Walking bass | Chords, Measures |
| `/drums` | Drum pattern | Style, Measures |
| `/arrange` | Full arrangement | Key, Style, Form, Measures |
| `/info` | Show score info | - |
| `/ping` | Check connection | - |

## 🎼 Parameters

### Keys
`C`, `D`, `E`, `F`, `G`, `A`, `B` + `m` for minor, `#`/`b` for sharps/flats
Example: `Dm`, `Bb`, `F#`, `Cm`

### Contours (Melodic Shape)
- `ascending` - Upward motion
- `descending` - Downward motion
- `arch` - Rise then fall ⌒
- `valley` - Fall then rise ⌄
- `static` - Small range

### Rhythm Density
- `sparse` - Long notes (half, whole)
- `moderate` - Quarter notes
- `dense` - Eighth, sixteenth notes

### Styles
- `pop` - I-V-vi-IV, catchy, simple
- `jazz` - ii-V-I, extended chords, swing
- `classical` - Functional harmony, voice leading
- `rock` - Power chords, strong beat
- `blues` - 12-bar, dominant 7ths
- `folk` - Simple, I-IV-V

### Forms
- `verse_chorus` - Modern pop/rock
- `ABA` - Ternary (statement, contrast, return)
- `AABA` - 32-bar standard
- `binary` - AB (two sections)
- `12_bar_blues` - Traditional blues

### Harmony Styles
- `thirds` - Sweet, close harmony
- `sixths` - Smooth, open sound
- `fourths` - Modal, folk
- `triads` - Full 3-note chords

## 🎵 Common Progressions

### Pop
- `I V vi IV` (C G Am F)
- `vi IV I V` (Am F C G)
- `I vi IV V` (C Am F G)

### Jazz
- `ii V I` (Dm7 G7 Cmaj7)
- `I VI ii V` (Cmaj7 A7 Dm7 G7)
- `iii VI ii V` (Em7 A7 Dm7 G7)

### Classical
- `I IV V I` (Authentic cadence)
- `I vi ii V` (Circle progression)

### Blues
- 12-bar: `I I I I | IV IV I I | V IV I V`

## 🎹 MIDI Pitch Reference

```
C2=36  Bass register
C3=48  Low
C4=60  Middle C ★
C5=72  Soprano
C6=84  High
```

Each octave = 12 semitones
Sharp (+1), Flat (-1)

## ⏱️ Duration (Ticks)

```
Whole    = 1920
Half     = 960
Quarter  = 480  ★ (common)
Eighth   = 240
Sixteenth = 120
```

## 🥁 Drum MIDI Notes

```
Kick (Bass Drum)    = 36
Snare               = 38
Hi-Hat Closed       = 42
Hi-Hat Open         = 46
Ride Cymbal         = 51
Crash Cymbal        = 49
Tom (High)          = 50
Tom (Mid)           = 47
Tom (Low)           = 45
```

## 📝 Example Workflows

### Quick Pop Song
```bash
>>> /arrange
Key: G, Style: pop, Form: verse_chorus, Measures: 16

>>> Compose catchy melody for verse (measures 0-7)

>>> /bass
Chords: G D Em C G D Em C G D C D G D Em C
Measures: 16

>>> /drums
Style: pop, Measures: 16
```

### Jazz Standard
```bash
>>> /progression
Key: Dm, Style: jazz, Measures: 32

>>> Create bebop melody with syncopation

>>> /bass
[Your generated chords], Measures: 32

>>> /drums
Style: jazz, Measures: 32
```

### Classical Piece
```bash
>>> Create classical ABA form in E♭, 24 measures

>>> Compose lyrical violin melody for A section

>>> Add dramatic contrast in B section (Cm)

>>> Add classical harmonization with voice leading
```

## 💡 Pro Tips

### Be Specific
❌ "Add notes"
✅ "Add C major ascending scale in quarter notes"

### Use Music Terms
- Intervals: "major third", "perfect fifth"
- Dynamics: "forte", "piano", "crescendo"
- Articulation: "staccato", "legato"

### Specify Register
```
>>> Bass notes in low register (C2-C3)
>>> Melody in soprano (C5-C6)
>>> Chords around middle C (C4)
```

### Work in Sections
```
>>> Verse: measures 0-7
>>> Chorus: measures 8-15
>>> Bridge: measures 16-23
```

### Iterate
```
>>> Add melody
>>> Make it more syncopated
>>> Add harmony in sixths
>>> Increase rhythm density
```

## ⚙️ Setup Checklist

- [ ] Python server running (`python main.py`)
- [ ] MuseScore open with score
- [ ] Plugin connected (green status)
- [ ] API key configured in `config.json`
- [ ] Score info sent to server (`/info`)

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Plugin disconnected | Check server is running, click Connect |
| No commands generated | Be more specific, use music terminology |
| Validation errors | Check measure numbers, pitch ranges |
| LLM timeout | Break into smaller requests |

## 🎓 Music Theory Quick Ref

### Chord Types
- Major: Root + M3 + P5 (C E G)
- Minor: Root + m3 + P5 (C Eb G)
- Dom7: Major + m7 (C E G Bb)
- Maj7: Major + M7 (C E G B)

### Scales
- Major: W W H W W W H
- Minor: W H W W H W W
- Pentatonic: R 2 3 5 6
- Blues: R ♭3 4 ♭5 5 ♭7

---

**Quick Start**: `/arrange` → Add melody → `/bass` → `/drums` → Done! 🎉

For full guide: See [COMPOSITION_GUIDE.md](COMPOSITION_GUIDE.md)
