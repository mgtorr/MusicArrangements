use crate::types::AtomicCommand;
use serde_json::Value;
use tracing::warn;

/// Valid duration values in ticks
const VALID_DURATIONS: &[u32] = &[60, 120, 180, 240, 360, 480, 720, 960, 1440, 1920];

/// Valid dynamic markings
const VALID_DYNAMICS: &[&str] = &[
    "pppp", "ppp", "pp", "p", "mp", "mf", "f", "ff", "fff", "ffff", "fp", "sfz", "sf", "rf", "rfz",
];

/// Validation constraints
const MAX_MIDI_PITCH: u8 = 127;
const MAX_MEASURE: u32 = 1000;
const MAX_TRACKS: u32 = 100;
const MIN_BPM: u32 = 20;
const MAX_BPM: u32 = 400;
const MAX_CHORD_NOTES: usize = 12;

/// Command validator
pub struct CommandValidator;

impl CommandValidator {
    pub fn new() -> Self {
        Self
    }

    /// Validate a single command
    pub fn validate_command(&self, cmd: &Value) -> Result<Value, String> {
        let cmd_type = cmd["type"]
            .as_str()
            .ok_or("Missing command type")?;

        match cmd_type {
            "add_note" => self.validate_add_note(cmd),
            "add_chord" => self.validate_add_chord(cmd),
            "add_rest" => self.validate_add_rest(cmd),
            "add_dynamic" => self.validate_add_dynamic(cmd),
            "add_tempo" => self.validate_add_tempo(cmd),
            "add_text" => self.validate_add_text(cmd),
            "transpose" => self.validate_transpose(cmd),
            _ => Err(format!("Unknown command type: {}", cmd_type)),
        }
    }

    /// Validate a list of commands, returning valid ones and errors
    pub fn validate_commands(&self, commands: &[Value]) -> (Vec<Value>, Vec<String>) {
        let mut valid = Vec::new();
        let mut errors = Vec::new();

        for cmd in commands {
            match self.validate_command(cmd) {
                Ok(validated) => valid.push(validated),
                Err(e) => {
                    warn!("Validation error: {}", e);
                    errors.push(e);
                }
            }
        }

        (valid, errors)
    }

    fn validate_add_note(&self, cmd: &Value) -> Result<Value, String> {
        let pitch = cmd["pitch"]
            .as_u64()
            .ok_or("Missing or invalid pitch")?;
        if pitch > MAX_MIDI_PITCH as u64 {
            return Err(format!("Pitch {} out of range (0-127)", pitch));
        }

        let duration = cmd["duration"]
            .as_u64()
            .ok_or("Missing or invalid duration")?;
        let duration = self.nearest_valid_duration(duration as u32);

        let measure = cmd["measure"].as_u64().unwrap_or(0);
        if measure > MAX_MEASURE as u64 {
            warn!("Measure {} exceeds recommended max", measure);
        }

        let track = cmd["track"].as_u64().unwrap_or(0);
        if track > MAX_TRACKS as u64 {
            return Err(format!("Track {} out of range (0-{})", track, MAX_TRACKS));
        }

        Ok(serde_json::json!({
            "type": "add_note",
            "pitch": pitch,
            "duration": duration,
            "measure": measure,
            "track": track
        }))
    }

    fn validate_add_chord(&self, cmd: &Value) -> Result<Value, String> {
        let pitches = cmd["pitches"]
            .as_array()
            .ok_or("Missing or invalid pitches array")?;

        if pitches.is_empty() {
            return Err("Chord must have at least one pitch".to_string());
        }

        let mut valid_pitches: Vec<u64> = Vec::new();
        for p in pitches.iter().take(MAX_CHORD_NOTES) {
            let pitch = p.as_u64().ok_or("Invalid pitch in chord")?;
            if pitch > MAX_MIDI_PITCH as u64 {
                return Err(format!("Pitch {} out of range (0-127)", pitch));
            }
            valid_pitches.push(pitch);
        }

        if pitches.len() > MAX_CHORD_NOTES {
            warn!(
                "Chord has {} notes, limiting to {}",
                pitches.len(),
                MAX_CHORD_NOTES
            );
        }

        let duration = cmd["duration"]
            .as_u64()
            .ok_or("Missing or invalid duration")?;
        let duration = self.nearest_valid_duration(duration as u32);

        let measure = cmd["measure"].as_u64().unwrap_or(0);
        let track = cmd["track"].as_u64().unwrap_or(0);

        Ok(serde_json::json!({
            "type": "add_chord",
            "pitches": valid_pitches,
            "duration": duration,
            "measure": measure,
            "track": track
        }))
    }

    fn validate_add_rest(&self, cmd: &Value) -> Result<Value, String> {
        let duration = cmd["duration"]
            .as_u64()
            .ok_or("Missing or invalid duration")?;
        let duration = self.nearest_valid_duration(duration as u32);

        let measure = cmd["measure"].as_u64().unwrap_or(0);
        let track = cmd["track"].as_u64().unwrap_or(0);

        Ok(serde_json::json!({
            "type": "add_rest",
            "duration": duration,
            "measure": measure,
            "track": track
        }))
    }

    fn validate_add_dynamic(&self, cmd: &Value) -> Result<Value, String> {
        let dynamic = cmd["dynamic"]
            .as_str()
            .ok_or("Missing or invalid dynamic")?
            .to_lowercase();

        if !VALID_DYNAMICS.contains(&dynamic.as_str()) {
            return Err(format!(
                "Invalid dynamic '{}'. Valid: {:?}",
                dynamic, VALID_DYNAMICS
            ));
        }

        let measure = cmd["measure"].as_u64().unwrap_or(0);
        let track = cmd["track"].as_u64().unwrap_or(0);

        Ok(serde_json::json!({
            "type": "add_dynamic",
            "dynamic": dynamic,
            "measure": measure,
            "track": track
        }))
    }

    fn validate_add_tempo(&self, cmd: &Value) -> Result<Value, String> {
        let bpm = cmd["bpm"]
            .as_u64()
            .ok_or("Missing or invalid BPM")?;

        let bpm = bpm.clamp(MIN_BPM as u64, MAX_BPM as u64);

        let measure = cmd["measure"].as_u64().unwrap_or(0);
        let text = cmd["text"].as_str().map(|s| s.to_string());

        let mut result = serde_json::json!({
            "type": "add_tempo",
            "bpm": bpm,
            "measure": measure
        });

        if let Some(t) = text {
            result["text"] = serde_json::Value::String(t);
        }

        Ok(result)
    }

    fn validate_add_text(&self, cmd: &Value) -> Result<Value, String> {
        let text = cmd["text"]
            .as_str()
            .ok_or("Missing or invalid text")?;

        if text.is_empty() {
            return Err("Text cannot be empty".to_string());
        }

        let measure = cmd["measure"].as_u64().unwrap_or(0);
        let track = cmd["track"].as_u64().unwrap_or(0);
        let text_type = cmd["textType"].as_str().map(|s| s.to_string());

        let mut result = serde_json::json!({
            "type": "add_text",
            "text": text,
            "measure": measure,
            "track": track
        });

        if let Some(tt) = text_type {
            result["textType"] = serde_json::Value::String(tt);
        }

        Ok(result)
    }

    fn validate_transpose(&self, cmd: &Value) -> Result<Value, String> {
        let semitones = cmd["semitones"]
            .as_i64()
            .ok_or("Missing or invalid semitones")?;

        if semitones < -24 || semitones > 24 {
            return Err(format!(
                "Semitones {} out of range (-24 to 24)",
                semitones
            ));
        }

        Ok(serde_json::json!({
            "type": "transpose",
            "semitones": semitones
        }))
    }

    /// Find the nearest valid duration
    fn nearest_valid_duration(&self, duration: u32) -> u32 {
        VALID_DURATIONS
            .iter()
            .min_by_key(|&&d| (d as i32 - duration as i32).abs())
            .copied()
            .unwrap_or(480) // Default to quarter note
    }
}

impl Default for CommandValidator {
    fn default() -> Self {
        Self::new()
    }
}
