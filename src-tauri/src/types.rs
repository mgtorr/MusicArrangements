use serde::{Deserialize, Serialize};

/// Score information from MuseScore
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ScoreInfo {
    pub title: String,
    pub composer: String,
    pub measures: u32,
    pub staves: u32,
    pub parts: Vec<PartInfo>,
    #[serde(rename = "timeSignature")]
    pub time_signature: Option<TimeSignature>,
    #[serde(rename = "keySignature")]
    pub key_signature: i32,
    pub tempo: Option<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PartInfo {
    pub name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TimeSignature {
    pub numerator: u32,
    pub denominator: u32,
}

/// Atomic music command
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum AtomicCommand {
    AddNote {
        pitch: u8,
        duration: u32,
        measure: u32,
        #[serde(default)]
        track: u32,
    },
    AddChord {
        pitches: Vec<u8>,
        duration: u32,
        measure: u32,
        #[serde(default)]
        track: u32,
    },
    AddRest {
        duration: u32,
        measure: u32,
        #[serde(default)]
        track: u32,
    },
    AddDynamic {
        dynamic: String,
        measure: u32,
        #[serde(default)]
        track: u32,
    },
    AddTempo {
        bpm: u32,
        measure: u32,
        #[serde(default)]
        text: Option<String>,
    },
    AddText {
        text: String,
        measure: u32,
        #[serde(default)]
        track: u32,
        #[serde(rename = "textType", default)]
        text_type: Option<String>,
    },
    Transpose {
        semitones: i32,
    },
}

impl AtomicCommand {
    /// Convert to a JSON object for sending to the plugin
    pub fn to_json(&self) -> serde_json::Value {
        serde_json::to_value(self).unwrap_or(serde_json::Value::Null)
    }
}

/// LLM response structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LLMResponse {
    pub intent: String,
    pub commands: Vec<serde_json::Value>,
    #[serde(default)]
    pub notes: Option<String>,
}

/// Result from processing a request
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessResult {
    pub success: bool,
    pub intent: Option<String>,
    pub commands_sent: Option<usize>,
    pub errors: Option<Vec<String>>,
    pub notes: Option<String>,
}

/// Generic command result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommandResult {
    pub success: bool,
    pub message: Option<String>,
    pub error: Option<String>,
}

impl CommandResult {
    pub fn ok(message: impl Into<String>) -> Self {
        Self {
            success: true,
            message: Some(message.into()),
            error: None,
        }
    }

    pub fn err(error: impl Into<String>) -> Self {
        Self {
            success: false,
            message: None,
            error: Some(error.into()),
        }
    }
}

/// Server status
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerStatus {
    pub running: bool,
    pub connected: bool,
    pub port: u16,
}

/// Duration constants (in ticks)
#[allow(dead_code)]
pub mod duration {
    pub const WHOLE: u32 = 1920;
    pub const HALF: u32 = 960;
    pub const QUARTER: u32 = 480;
    pub const EIGHTH: u32 = 240;
    pub const SIXTEENTH: u32 = 120;
    pub const THIRTYSECOND: u32 = 60;
    pub const DOTTED_HALF: u32 = 1440;
    pub const DOTTED_QUARTER: u32 = 720;
    pub const DOTTED_EIGHTH: u32 = 360;
}

/// MIDI pitch helpers
pub mod pitch {
    pub fn note_name_to_midi(name: &str) -> Option<u8> {
        let name = name.trim();
        if name.is_empty() {
            return None;
        }

        let mut chars = name.chars();
        let note = chars.next()?.to_ascii_uppercase();
        let rest: String = chars.collect();

        let base = match note {
            'C' => 0,
            'D' => 2,
            'E' => 4,
            'F' => 5,
            'G' => 7,
            'A' => 9,
            'B' => 11,
            _ => return None,
        };

        let mut offset: i8 = 0;
        let mut octave_str = String::new();

        for c in rest.chars() {
            match c {
                '#' | '+' => offset += 1,
                'b' | '-' => offset -= 1,
                '0'..='9' => octave_str.push(c),
                _ => {}
            }
        }

        let octave: i8 = octave_str.parse().unwrap_or(4);
        let midi = (octave + 1) * 12 + base + offset;

        if midi >= 0 && midi <= 127 {
            Some(midi as u8)
        } else {
            None
        }
    }

    pub fn midi_to_note_name(midi: u8) -> String {
        let note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
        let octave = (midi / 12) as i8 - 1;
        let note = (midi % 12) as usize;
        format!("{}{}", note_names[note], octave)
    }
}
