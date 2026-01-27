use crate::types::{LLMResponse, ScoreInfo};
use serde_json::json;
use tracing::{debug, error};

/// LLM provider type
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum LLMProvider {
    Claude,
    Gemini,
    OpenAI,
}

impl LLMProvider {
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "claude" | "anthropic" => Some(Self::Claude),
            "gemini" | "google" => Some(Self::Gemini),
            "openai" | "gpt" => Some(Self::OpenAI),
            _ => None,
        }
    }
}

/// LLM interpreter for natural language to music commands
#[derive(Clone)]
pub struct LLMInterpreter {
    provider: LLMProvider,
    api_key: String,
    model: String,
    client: reqwest::Client,
}

impl LLMInterpreter {
    pub fn new(provider: LLMProvider, api_key: String, model: String) -> Self {
        Self {
            provider,
            api_key,
            model,
            client: reqwest::Client::new(),
        }
    }

    pub fn set_provider(&mut self, provider: LLMProvider, api_key: String, model: String) {
        self.provider = provider;
        self.api_key = api_key;
        self.model = model;
    }

    /// Interpret a natural language request
    pub async fn interpret(
        &self,
        request: &str,
        score_info: Option<&ScoreInfo>,
    ) -> Result<LLMResponse, String> {
        let system_prompt = self.build_system_prompt(score_info);
        let user_prompt = request;

        match self.provider {
            LLMProvider::Claude => self.call_claude(&system_prompt, user_prompt).await,
            LLMProvider::Gemini => self.call_gemini(&system_prompt, user_prompt).await,
            LLMProvider::OpenAI => self.call_openai(&system_prompt, user_prompt).await,
        }
    }

    fn build_system_prompt(&self, score_info: Option<&ScoreInfo>) -> String {
        let mut prompt = r#"You are a music composition assistant. Convert natural language requests into atomic music commands.

Available commands:
1. add_note: { "type": "add_note", "pitch": <MIDI 0-127>, "duration": <ticks>, "measure": <0-based>, "track": <0-based> }
2. add_chord: { "type": "add_chord", "pitches": [<MIDI>...], "duration": <ticks>, "measure": <0-based>, "track": <0-based> }
3. add_rest: { "type": "add_rest", "duration": <ticks>, "measure": <0-based>, "track": <0-based> }
4. add_dynamic: { "type": "add_dynamic", "dynamic": "<pp|p|mp|mf|f|ff|etc>", "measure": <0-based>, "track": <0-based> }
5. add_tempo: { "type": "add_tempo", "bpm": <20-400>, "measure": <0-based>, "text": "<optional>" }
6. add_text: { "type": "add_text", "text": "<text>", "measure": <0-based>, "track": <0-based> }
7. transpose: { "type": "transpose", "semitones": <-24 to 24> }

MIDI pitch reference: C4(middle C)=60, D4=62, E4=64, F4=65, G4=67, A4=69, B4=71
Duration reference: whole=1920, half=960, quarter=480, eighth=240, sixteenth=120

Common chords (starting from C4=60):
- C major: [60, 64, 67]
- C minor: [60, 63, 67]
- G major: [55, 59, 62] or [67, 71, 74]
- D major: [62, 66, 69]
- A minor: [57, 60, 64] or [69, 72, 76]
- F major: [53, 57, 60] or [65, 69, 72]

Respond ONLY with valid JSON in this exact format:
{
  "intent": "<brief description of what you're doing>",
  "commands": [<array of command objects>],
  "notes": "<optional notes about limitations or suggestions>"
}
"#.to_string();

        if let Some(info) = score_info {
            prompt.push_str(&format!(
                r#"

Current score context:
- Title: {}
- Measures: {}
- Staves: {}
- Time signature: {}/{}
- Key signature: {} sharps/flats
"#,
                info.title,
                info.measures,
                info.staves,
                info.time_signature.as_ref().map(|t| t.numerator).unwrap_or(4),
                info.time_signature.as_ref().map(|t| t.denominator).unwrap_or(4),
                info.key_signature
            ));
        }

        prompt
    }

    async fn call_claude(&self, system: &str, user: &str) -> Result<LLMResponse, String> {
        let response = self
            .client
            .post("https://api.anthropic.com/v1/messages")
            .header("x-api-key", &self.api_key)
            .header("anthropic-version", "2023-06-01")
            .header("content-type", "application/json")
            .json(&json!({
                "model": self.model,
                "max_tokens": 2048,
                "system": system,
                "messages": [
                    { "role": "user", "content": user }
                ]
            }))
            .send()
            .await
            .map_err(|e| format!("Request failed: {}", e))?;

        let status = response.status();
        let body = response
            .text()
            .await
            .map_err(|e| format!("Failed to read response: {}", e))?;

        debug!("Claude response ({}): {}", status, body);

        if !status.is_success() {
            return Err(format!("API error ({}): {}", status, body));
        }

        let json: serde_json::Value =
            serde_json::from_str(&body).map_err(|e| format!("JSON parse error: {}", e))?;

        let content = json["content"][0]["text"]
            .as_str()
            .ok_or("No content in response")?;

        self.parse_llm_response(content)
    }

    async fn call_gemini(&self, system: &str, user: &str) -> Result<LLMResponse, String> {
        let url = format!(
            "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent?key={}",
            self.model, self.api_key
        );

        let response = self
            .client
            .post(&url)
            .header("content-type", "application/json")
            .json(&json!({
                "contents": [
                    {
                        "parts": [
                            { "text": format!("{}\n\nUser request: {}", system, user) }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048
                }
            }))
            .send()
            .await
            .map_err(|e| format!("Request failed: {}", e))?;

        let status = response.status();
        let body = response
            .text()
            .await
            .map_err(|e| format!("Failed to read response: {}", e))?;

        debug!("Gemini response ({}): {}", status, body);

        if !status.is_success() {
            return Err(format!("API error ({}): {}", status, body));
        }

        let json: serde_json::Value =
            serde_json::from_str(&body).map_err(|e| format!("JSON parse error: {}", e))?;

        let content = json["candidates"][0]["content"]["parts"][0]["text"]
            .as_str()
            .ok_or("No content in response")?;

        self.parse_llm_response(content)
    }

    async fn call_openai(&self, system: &str, user: &str) -> Result<LLMResponse, String> {
        let response = self
            .client
            .post("https://api.openai.com/v1/chat/completions")
            .header("Authorization", format!("Bearer {}", self.api_key))
            .header("content-type", "application/json")
            .json(&json!({
                "model": self.model,
                "max_tokens": 2048,
                "messages": [
                    { "role": "system", "content": system },
                    { "role": "user", "content": user }
                ]
            }))
            .send()
            .await
            .map_err(|e| format!("Request failed: {}", e))?;

        let status = response.status();
        let body = response
            .text()
            .await
            .map_err(|e| format!("Failed to read response: {}", e))?;

        debug!("OpenAI response ({}): {}", status, body);

        if !status.is_success() {
            return Err(format!("API error ({}): {}", status, body));
        }

        let json: serde_json::Value =
            serde_json::from_str(&body).map_err(|e| format!("JSON parse error: {}", e))?;

        let content = json["choices"][0]["message"]["content"]
            .as_str()
            .ok_or("No content in response")?;

        self.parse_llm_response(content)
    }

    fn parse_llm_response(&self, content: &str) -> Result<LLMResponse, String> {
        // Try to extract JSON from the response
        let json_str = if let Some(start) = content.find('{') {
            if let Some(end) = content.rfind('}') {
                &content[start..=end]
            } else {
                content
            }
        } else {
            content
        };

        serde_json::from_str(json_str).map_err(|e| {
            error!("Failed to parse LLM response: {}\nContent: {}", e, content);
            format!("Failed to parse response: {}", e)
        })
    }
}

impl Default for LLMInterpreter {
    fn default() -> Self {
        Self::new(
            LLMProvider::Claude,
            String::new(),
            "claude-sonnet-4-20250514".to_string(),
        )
    }
}
