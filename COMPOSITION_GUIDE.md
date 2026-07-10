# MuseScore Composition Assistant Guide

## Introduction

The MuseScore LLM Bridge now includes an advanced **Composition Assistant** that transforms natural language requests into musical arrangements. It combines AI language models with music theory intelligence to help you compose, arrange, and orchestrate music.

## Key Capabilities

### 1. Natural Language Understanding

The system understands music terminology and concepts:

```
>>> Create a jazz ii-V-I progression in F major
>>> Add a melancholy melody in D minor with descending motion
>>> Harmonize this melody using thirds
>>> Generate a 16-bar verse-chorus pop song in G
```

### 2. Music Theory Intelligence

The LLM has deep knowledge of:
- **Harmony**: Functional harmony, chord progressions, voice leading
- **Counterpoint**: Independent melodic lines, contrary motion
- **Form**: Song structures (verse-chorus, ABA, Rondo, etc.)
- **Style**: Jazz, Classical, Pop, Rock, Blues, Folk characteristics
- **Orchestration**: Instrument ranges, timbres, combinations

### 3. Context-Aware Composition

The assistant considers:
- Current key signature
- Time signature
- Existing measures
- Parts/instruments in the score
- Style and mood of the piece

## Composition Features

### Melody Generation

Create melodic lines with specific characteristics:

```
>>> /melody
Key: G
Contour: arch               # ascending → descending shape
Measures: 8
Density: moderate          # note rhythm density
```

**Contour Types:**
- `ascending`: Upward melodic motion
- `descending`: Downward motion
- `arch`: Rise then fall (classical phrasing)
- `valley`: Fall then rise
- `static`: Small-range meandering

**Rhythm Density:**
- `sparse`: Longer note values (half notes, whole notes)
- `moderate`: Quarter notes with some eighths
- `dense`: Eighth notes, sixteenths

**Natural Language:**
```
>>> Compose a lyrical melody in E♭ with an arch shape
>>> Create an ascending melodic line spanning 2 octaves
>>> Add a simple, sparse melody for the verse
```

### Chord Progressions

Generate harmonic progressions in various styles:

```
>>> /progression
Key: C
Style: jazz
Measures: 8
```

**Available Styles:**
- **Pop**: I-V-vi-IV, I-vi-IV-V (familiar, catchy)
- **Jazz**: ii-V-I, iii-VI-ii-V (extended chords, substitutions)
- **Classical**: I-IV-V-I, functional harmony
- **Blues**: 12-bar blues with dominant 7ths
- **Folk**: Simple I-IV-V patterns

**Example Output:**
```
Pop in C: C → G → Am → F
Jazz in Dm: Dm7 → G7 → Cmaj7 → A7
Blues in G: G7 → G7 → G7 → G7 → C7 → C7 → G7 → G7 → D7 → C7 → G7 → D7
```

**Natural Language:**
```
>>> Add a ii-V-I progression in B♭
>>> Create a 12-bar blues progression
>>> Generate a sad chord progression in A minor
```

### Harmonization

Add harmony voices to existing melodies:

**Harmony Styles:**
- **Thirds**: Parallel thirds (sweet, close harmony)
- **Sixths**: Parallel sixths (smooth, open)
- **Fourths**: Fourths below (modal, folk sound)
- **Triads**: Full 3-note chords (rich harmony)

**Natural Language:**
```
>>> Harmonize the melody in thirds
>>> Add a harmony line a sixth below
>>> Create 4-part vocal harmonization
```

### Walking Bass Lines

Automatically generate bass patterns:

```
>>> /bass
Chords: G C D G
Measures: 4
```

The system generates:
- Root notes on strong beats
- Chord tones (root, 3rd, 5th)
- Passing tones for melodic connection
- Chromatic approach notes

**Natural Language:**
```
>>> Add a walking bass line over these chords
>>> Create a simple bass following chord roots
>>> Generate a funky bass pattern
```

### Drum Patterns

Create rhythm section grooves:

```
>>> /drums
Style: jazz
Measures: 8
```

**Available Styles:**
- **Rock**: Heavy kick on 1 & 3, snare on 2 & 4, steady hi-hat
- **Jazz**: Swing ride, light kick, snare hits on 2.5 & 4.5
- **Pop**: Backbeat emphasis, consistent hi-hat pattern
- **Latin**: Syncopated kick, clave-inspired snare
- **Metal**: Double kick, fast hi-hat 16ths

**Natural Language:**
```
>>> Add a jazz swing drum pattern
>>> Create rock drums with a heavy groove
>>> Generate a Latin percussion rhythm
```

### Full Arrangements

Create complete multi-section compositions:

```
>>> /arrange
Key: G
Style: pop
Form: verse_chorus
Total measures: 16
```

**Form Types:**
- **verse_chorus**: Modern pop/rock structure
- **ABA**: Ternary form (statement, contrast, return)
- **AABA**: 32-bar standard (Tin Pan Alley, jazz)
- **binary**: AB (two contrasting sections)
- **12_bar_blues**: Traditional blues structure

The arranger:
1. Divides measures into sections
2. Generates appropriate progressions for each section
3. Can add melodies, bass, and drums per section
4. Maintains coherence between sections

**Natural Language:**
```
>>> Create a pop song arrangement with verse and chorus
>>> Generate a classical ABA form piece
>>> Build a 12-bar blues arrangement
```

## Advanced Composition Techniques

### Voice Leading

The system follows classical voice leading rules:

- **Smooth Motion**: Voices move by smallest interval
- **Contrary Motion**: Outer voices move in opposite directions
- **Avoid Parallels**: No parallel 5ths or octaves
- **Range**: Keep voices in comfortable register

**Example:**
```
>>> Add 4-part harmony with proper voice leading
>>> Harmonize using smooth voice motion
```

### Style-Specific Composition

When you mention a style, the LLM applies appropriate characteristics:

**Classical:**
- Balanced phrases (4+4, 8+8 measures)
- Functional harmony (I-IV-V)
- Clear cadences
- Sophisticated voice leading

**Jazz:**
- Extended chords (7ths, 9ths, 11ths, 13ths)
- ii-V-I progressions
- Tritone substitutions
- Swing rhythms
- Walking bass

**Pop:**
- Simple, memorable progressions
- Repetitive hooks
- 4/4 time, backbeat
- Accessible melodies

**Blues:**
- 12-bar form
- Blue notes (♭3, ♭5, ♭7)
- Dominant 7th chords
- Pentatonic scales
- Call-and-response

### Multi-Track Arrangements

The system can work with multiple tracks:

```
>>> Add melody on track 0
>>> Add harmony on track 1  
>>> Add bass on track 2
>>> Add drums on track 3 (uses drum pitches)
```

## Workflow Examples

### Example 1: Pop Song from Scratch

```
# 1. Create arrangement structure
>>> /arrange
Key: C
Style: pop
Form: verse_chorus
Total measures: 16

# 2. Add verse melody
>>> Compose a catchy melody for measures 0-7

# 3. Add chorus melody
>>> Create an uplifting melody for measures 8-15 with higher register

# 4. Add bass
>>> /bass
Chords: C G Am F C G Am F C G F G C G Am F
Measures: 16

# 5. Add drums
>>> /drums
Style: pop
Measures: 16

# 6. Add dynamics
>>> Add crescendo from mp to f at measure 8
```

### Example 2: Jazz Composition

```
# 1. Set up progression
>>> /progression
Key: Dm  
Style: jazz
Measures: 32

# 2. Add jazz melody with bebop characteristics
>>> Compose a jazz melody with syncopation and chromatic passing tones

# 3. Add walking bass
>>> /bass
Chords: [your generated progression]
Measures: 32

# 4. Add swing drums
>>> /drums
Style: jazz
Measures: 32

# 5. Add harmonization
>>> Add jazz voicings with 7th chords
```

### Example 3: Classical Chamber Piece

```
# 1. Create ternary form
>>> Create a classical ABA form in G major, 24 measures

# 2. Violin melody (A section)
>>> Compose an elegant violin melody for measures 0-7, track 0

# 3. Contrasting middle (B section)
>>> Add a dramatic melody in E minor for measures 8-15, track 0

# 4. Return of A section
>>> Repeat the opening melody for measures 16-23

# 5. Add cello accompaniment
>>> Add cello arpeggios on track 1 following the harmony

# 6. Add viola inner voice
>>> Add viola harmony on track 2 with smooth voice leading
```

## Tips for Best Results

### 1. Be Specific
```
❌ "Add some notes"
✅ "Add a C major scale ascending over 2 measures"

❌ "Make it sound good"
✅ "Add a jazz ii-V-I progression with dominant 7th chords"
```

### 2. Use Music Terminology
The LLM understands:
- Intervals: "major third", "perfect fifth"
- Chord types: "major 7th", "diminished", "augmented"
- Dynamics: "piano", "forte", "crescendo"
- Articulation: "staccato", "legato"
- Form: "verse", "chorus", "bridge", "coda"

### 3. Specify Register/Octave
```
>>> Add bass notes in low register (C2-C3)
>>> Create melody in soprano range (C5-C6)
>>> Place chords in middle register around C4
```

### 4. Iterate and Refine
```
>>> Add a melody
>>> Make the melody more rhythmically interesting
>>> Change the rhythm to use more eighth notes
>>> Add syncopation
```

### 5. Work Section by Section
```
>>> Create verse in measures 0-7
>>> Create chorus in measures 8-15
>>> Create bridge in measures 16-19
>>> Return to chorus for measures 20-27
```

## Music Theory Reference

### Common Progressions

**Pop:**
- I - V - vi - IV (C - G - Am - F)
- I - vi - IV - V (C - Am - F - G)
- vi - IV - I - V (Am - F - C - G)

**Jazz:**
- ii - V - I (Dm7 - G7 - Cmaj7)
- I - VI - ii - V (Cmaj7 - A7 - Dm7 - G7)
- iii - VI - ii - V (Em7 - A7 - Dm7 - G7)

**Classical:**
- I - IV - V - I (Authentic cadence)
- I - vi - ii - V (Circle progression)

**Blues:**
- I7 - I7 - I7 - I7
- IV7 - IV7 - I7 - I7  
- V7 - IV7 - I7 - V7

### Chord Types

- **Major**: Root, major 3rd, perfect 5th (C-E-G)
- **Minor**: Root, minor 3rd, perfect 5th (C-E♭-G)
- **Dominant 7th**: Major triad + minor 7th (C-E-G-B♭)
- **Major 7th**: Major triad + major 7th (C-E-G-B)
- **Minor 7th**: Minor triad + minor 7th (C-E♭-G-B♭)
- **Diminished**: Root, minor 3rd, diminished 5th (C-E♭-G♭)
- **Augmented**: Root, major 3rd, augmented 5th (C-E-G#)

### Scales

- **Major**: W-W-H-W-W-W-H (C-D-E-F-G-A-B)
- **Natural Minor**: W-H-W-W-H-W-W (A-B-C-D-E-F-G)
- **Harmonic Minor**: W-H-W-W-H-WH-H (raise 7th)
- **Melodic Minor**: W-H-W-W-W-W-H (raise 6th and 7th ascending)
- **Pentatonic Major**: Root-2-3-5-6 (C-D-E-G-A)
- **Blues**: Root-♭3-4-♭5-5-♭7 (C-E♭-F-G♭-G-B♭)

### MIDI Pitch Reference

```
Octave 6: C6=84  D6=86  E6=88  F6=89  G6=91  A6=93  B6=95
Octave 5: C5=72  D5=74  E5=76  F5=77  G5=79  A5=81  B5=83
Octave 4: C4=60  D4=62  E4=64  F4=65  G4=67  A4=69  B4=71  (Middle C)
Octave 3: C3=48  D3=50  E3=52  F3=53  G3=55  A3=57  B3=59
Octave 2: C2=36  D2=38  E2=40  F2=41  G2=43  A2=45  B2=47  (Bass)
```

### Duration Reference (MuseScore Ticks)

```
Whole Note       = 1920 ticks
Dotted Half      = 1440 ticks
Half Note        = 960 ticks
Dotted Quarter   = 720 ticks
Quarter Note     = 480 ticks
Dotted Eighth    = 360 ticks
Eighth Note      = 240 ticks
Sixteenth Note   = 120 ticks
```

## Troubleshooting

### "No commands generated"
- Make request more specific with musical details
- Specify key, measures, and track
- Try breaking into smaller requests

### "Commands validation failed"
- Check measure numbers (0-indexed)
- Verify pitch ranges (0-127 MIDI)
- Ensure duration values are valid

### "LLM not understanding musical concept"
- Use standard music terminology
- Provide more context (key, style, form)
- Try rephrasing with specific examples

### "Melody doesn't fit harmony"
- Generate harmony first, then melody
- Or use "harmonize this melody" after creating melody
- Specify "melody should follow chord tones"

## Going Further

### Experiment with Styles

Mix and match elements:
```
>>> Add a jazz melody over a rock chord progression
>>> Create classical-style voice leading in a pop song
>>> Generate a blues melody with electronic synth pads
```

### Build Incrementally

Start simple and add layers:
```
>>> Start with simple I-IV-V progression
>>> Add a basic melody
>>> Add harmony in thirds
>>> Add walking bass
>>> Add drums
>>> Add dynamics and articulation
>>> Add intro and outro
```

### Learn from Examples

Ask the assistant to explain:
```
>>> Explain the voice leading in this progression
>>> Why does this chord progression work?
>>> What makes this melody effective?
>>> Show me the harmonic function of each chord
```

## Conclusion

The Composition Assistant combines:
- **AI Language Understanding** (Claude/Gemini/OpenAI)
- **Music Theory Intelligence** (Specialized prompts)
- **Algorithmic Composition** (Music21 + custom generators)
- **Direct MuseScore Control** (QML bridge)

This creates a powerful tool that understands **what** you want musically and knows **how** to create it technically.

Happy composing! 🎵
