use crate::types::{duration, pitch, AtomicCommand};

/// Scale types
#[derive(Debug, Clone, Copy)]
pub enum Scale {
    Major,
    Minor,
    HarmonicMinor,
    Blues,
    Pentatonic,
}

impl Scale {
    pub fn intervals(&self) -> &[i32] {
        match self {
            Scale::Major => &[0, 2, 4, 5, 7, 9, 11],
            Scale::Minor => &[0, 2, 3, 5, 7, 8, 10],
            Scale::HarmonicMinor => &[0, 2, 3, 5, 7, 8, 11],
            Scale::Blues => &[0, 3, 5, 6, 7, 10],
            Scale::Pentatonic => &[0, 2, 4, 7, 9],
        }
    }
}

/// Chord types
#[derive(Debug, Clone, Copy)]
pub enum ChordType {
    Major,
    Minor,
    Diminished,
    Augmented,
    Maj7,
    Min7,
    Dom7,
    Sus2,
    Sus4,
    Add9,
    Power,
}

impl ChordType {
    pub fn intervals(&self) -> &[i32] {
        match self {
            ChordType::Major => &[0, 4, 7],
            ChordType::Minor => &[0, 3, 7],
            ChordType::Diminished => &[0, 3, 6],
            ChordType::Augmented => &[0, 4, 8],
            ChordType::Maj7 => &[0, 4, 7, 11],
            ChordType::Min7 => &[0, 3, 7, 10],
            ChordType::Dom7 => &[0, 4, 7, 10],
            ChordType::Sus2 => &[0, 2, 7],
            ChordType::Sus4 => &[0, 5, 7],
            ChordType::Add9 => &[0, 4, 7, 14],
            ChordType::Power => &[0, 7],
        }
    }

    pub fn from_str(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "m" | "min" | "minor" => ChordType::Minor,
            "dim" | "diminished" => ChordType::Diminished,
            "aug" | "augmented" => ChordType::Augmented,
            "maj7" => ChordType::Maj7,
            "m7" | "min7" => ChordType::Min7,
            "7" | "dom7" => ChordType::Dom7,
            "sus2" => ChordType::Sus2,
            "sus4" => ChordType::Sus4,
            "add9" => ChordType::Add9,
            "5" | "power" => ChordType::Power,
            _ => ChordType::Major,
        }
    }
}

/// Drum kit MIDI notes (General MIDI standard)
pub mod drums {
    pub const KICK: u8 = 36;
    pub const SNARE: u8 = 38;
    pub const CLOSED_HIHAT: u8 = 42;
    pub const OPEN_HIHAT: u8 = 46;
    pub const RIDE: u8 = 51;
    pub const CRASH: u8 = 49;
    pub const TOM_HIGH: u8 = 50;
    pub const TOM_MID: u8 = 47;
    pub const TOM_LOW: u8 = 45;
}

/// Drum pattern styles
#[derive(Debug, Clone, Copy)]
pub enum DrumStyle {
    Rock,
    Jazz,
    Pop,
    Latin,
    Metal,
}

impl DrumStyle {
    pub fn from_str(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "jazz" => DrumStyle::Jazz,
            "pop" => DrumStyle::Pop,
            "latin" => DrumStyle::Latin,
            "metal" => DrumStyle::Metal,
            _ => DrumStyle::Rock,
        }
    }
}

/// Music generator for creating patterns
pub struct MusicGenerator {
    key_root: u8,
    time_numerator: u32,
}

impl MusicGenerator {
    pub fn new(key_root: u8, time_numerator: u32) -> Self {
        Self {
            key_root,
            time_numerator,
        }
    }

    /// Generate a walking bass line
    pub fn walking_bass_line(
        &self,
        chords: &[String],
        measures: u32,
        track: u32,
    ) -> Vec<AtomicCommand> {
        let mut commands = Vec::new();
        let beats_per_measure = self.time_numerator;
        let duration = duration::QUARTER;

        for measure in 0..measures {
            let chord_idx = (measure as usize) % chords.len();
            let chord_name = &chords[chord_idx];

            // Parse chord name to get root and type
            let (root, chord_type) = parse_chord_name(chord_name);
            let root_pitch = pitch::note_name_to_midi(&format!("{}2", root)).unwrap_or(36);

            // Get chord tones
            let intervals = chord_type.intervals();

            // Walking bass pattern: root, 3rd, 5th, approach note
            let pattern: Vec<u8> = if beats_per_measure >= 4 {
                vec![
                    root_pitch,
                    root_pitch.saturating_add(intervals.get(1).copied().unwrap_or(4) as u8),
                    root_pitch.saturating_add(intervals.get(2).copied().unwrap_or(7) as u8),
                    // Approach note (half step below next root)
                    {
                        let next_chord_idx = ((measure + 1) as usize) % chords.len();
                        let next_root = parse_chord_name(&chords[next_chord_idx]).0;
                        pitch::note_name_to_midi(&format!("{}2", next_root))
                            .unwrap_or(root_pitch)
                            .saturating_sub(1)
                    },
                ]
            } else {
                // For 3/4 or other time signatures
                vec![
                    root_pitch,
                    root_pitch.saturating_add(intervals.get(1).copied().unwrap_or(4) as u8),
                    root_pitch.saturating_add(intervals.get(2).copied().unwrap_or(7) as u8),
                ]
            };

            for (beat, &pitch) in pattern.iter().take(beats_per_measure as usize).enumerate() {
                commands.push(AtomicCommand::AddNote {
                    pitch,
                    duration,
                    measure,
                    track,
                });
            }
        }

        commands
    }

    /// Generate a drum pattern
    pub fn drum_pattern(&self, style: DrumStyle, measures: u32, track: u32) -> Vec<AtomicCommand> {
        let mut commands = Vec::new();
        let eighth = duration::EIGHTH;
        let sixteenth = duration::SIXTEENTH;

        for measure in 0..measures {
            match style {
                DrumStyle::Rock => {
                    // Kick on 1, 3; Snare on 2, 4; Hi-hat on all 8ths
                    for beat in 0..8 {
                        // Hi-hat on all 8th notes
                        commands.push(AtomicCommand::AddNote {
                            pitch: drums::CLOSED_HIHAT,
                            duration: eighth,
                            measure,
                            track,
                        });
                        // Kick on beats 1, 3 (0, 4 in 8th note terms)
                        if beat == 0 || beat == 4 {
                            commands.push(AtomicCommand::AddNote {
                                pitch: drums::KICK,
                                duration: eighth,
                                measure,
                                track,
                            });
                        }
                        // Snare on beats 2, 4 (2, 6 in 8th note terms)
                        if beat == 2 || beat == 6 {
                            commands.push(AtomicCommand::AddNote {
                                pitch: drums::SNARE,
                                duration: eighth,
                                measure,
                                track,
                            });
                        }
                    }
                }
                DrumStyle::Jazz => {
                    // Ride on all beats; kick on 1; snare on 2.5, 4.5
                    for beat in 0..4 {
                        commands.push(AtomicCommand::AddNote {
                            pitch: drums::RIDE,
                            duration: duration::QUARTER,
                            measure,
                            track,
                        });
                        if beat == 0 {
                            commands.push(AtomicCommand::AddNote {
                                pitch: drums::KICK,
                                duration: duration::QUARTER,
                                measure,
                                track,
                            });
                        }
                        if beat == 1 || beat == 3 {
                            commands.push(AtomicCommand::AddNote {
                                pitch: drums::CLOSED_HIHAT,
                                duration: duration::QUARTER,
                                measure,
                                track,
                            });
                        }
                    }
                }
                DrumStyle::Pop => {
                    // Similar to rock but with kick variations
                    for beat in 0..8 {
                        commands.push(AtomicCommand::AddNote {
                            pitch: drums::CLOSED_HIHAT,
                            duration: eighth,
                            measure,
                            track,
                        });
                        if beat == 0 || beat == 3 || beat == 4 {
                            commands.push(AtomicCommand::AddNote {
                                pitch: drums::KICK,
                                duration: eighth,
                                measure,
                                track,
                            });
                        }
                        if beat == 2 || beat == 6 {
                            commands.push(AtomicCommand::AddNote {
                                pitch: drums::SNARE,
                                duration: eighth,
                                measure,
                                track,
                            });
                        }
                    }
                }
                DrumStyle::Latin => {
                    // Syncopated pattern
                    for beat in 0..8 {
                        commands.push(AtomicCommand::AddNote {
                            pitch: drums::CLOSED_HIHAT,
                            duration: eighth,
                            measure,
                            track,
                        });
                        if beat == 0 || beat == 3 || beat == 6 {
                            commands.push(AtomicCommand::AddNote {
                                pitch: drums::KICK,
                                duration: eighth,
                                measure,
                                track,
                            });
                        }
                        if beat == 2 || beat == 5 {
                            commands.push(AtomicCommand::AddNote {
                                pitch: drums::SNARE,
                                duration: eighth,
                                measure,
                                track,
                            });
                        }
                    }
                }
                DrumStyle::Metal => {
                    // Fast kick drum, snare on 2 and 4
                    for beat in 0..16 {
                        commands.push(AtomicCommand::AddNote {
                            pitch: drums::CLOSED_HIHAT,
                            duration: sixteenth,
                            measure,
                            track,
                        });
                        commands.push(AtomicCommand::AddNote {
                            pitch: drums::KICK,
                            duration: sixteenth,
                            measure,
                            track,
                        });
                        if beat == 4 || beat == 12 {
                            commands.push(AtomicCommand::AddNote {
                                pitch: drums::SNARE,
                                duration: sixteenth,
                                measure,
                                track,
                            });
                        }
                    }
                }
            }
        }

        commands
    }
}

/// Parse a chord name into root and type
fn parse_chord_name(name: &str) -> (String, ChordType) {
    let name = name.trim();
    if name.is_empty() {
        return ("C".to_string(), ChordType::Major);
    }

    let mut chars = name.chars().peekable();
    let mut root = chars.next().unwrap().to_string();

    // Check for sharps/flats
    if let Some(&c) = chars.peek() {
        if c == '#' || c == 'b' {
            root.push(chars.next().unwrap());
        }
    }

    // Rest is the chord type
    let type_str: String = chars.collect();
    let chord_type = ChordType::from_str(&type_str);

    (root, chord_type)
}

/// Get scale pitches for a given root and scale type
pub fn get_scale_pitches(root: u8, scale: Scale, octaves: u8) -> Vec<u8> {
    let intervals = scale.intervals();
    let mut pitches = Vec::new();

    for octave in 0..octaves {
        for &interval in intervals {
            let pitch = root as i32 + (octave as i32 * 12) + interval;
            if pitch >= 0 && pitch <= 127 {
                pitches.push(pitch as u8);
            }
        }
    }

    pitches
}

/// Get chord pitches for a given root and chord type
pub fn get_chord_pitches(root: u8, chord_type: ChordType) -> Vec<u8> {
    chord_type
        .intervals()
        .iter()
        .filter_map(|&interval| {
            let pitch = root as i32 + interval;
            if pitch >= 0 && pitch <= 127 {
                Some(pitch as u8)
            } else {
                None
            }
        })
        .collect()
}

/// Transpose pitches by semitones
pub fn transpose_pitches(pitches: &[u8], semitones: i32) -> Vec<u8> {
    pitches
        .iter()
        .filter_map(|&p| {
            let new_pitch = p as i32 + semitones;
            if new_pitch >= 0 && new_pitch <= 127 {
                Some(new_pitch as u8)
            } else {
                None
            }
        })
        .collect()
}

impl Default for MusicGenerator {
    fn default() -> Self {
        Self::new(60, 4) // C4, 4/4 time
    }
}
