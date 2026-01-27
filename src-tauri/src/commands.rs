use crate::bridge::BridgeServer;
use crate::config::Config;
use crate::llm::{LLMInterpreter, LLMProvider};
use crate::music::{DrumStyle, MusicGenerator};
use crate::types::{CommandResult, ProcessResult, ServerStatus};
use crate::validator::CommandValidator;
use crate::ws_bridge::WsBridgeServer;
use parking_lot::RwLock;
use std::sync::Arc;
use tauri::State;
use tracing::{debug, error, info};

/// Server type enum
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum ServerType {
    Http,
    WebSocket,
}

/// Bridge server wrapper that can be either HTTP or WebSocket
pub enum BridgeWrapper {
    Http(BridgeServer),
    WebSocket(WsBridgeServer),
}

impl BridgeWrapper {
    pub fn is_running(&self) -> bool {
        match self {
            BridgeWrapper::Http(s) => s.is_running(),
            BridgeWrapper::WebSocket(s) => s.is_running(),
        }
    }

    pub fn is_connected(&self) -> bool {
        match self {
            BridgeWrapper::Http(s) => s.is_connected(),
            BridgeWrapper::WebSocket(s) => s.is_connected(),
        }
    }

    pub fn port(&self) -> u16 {
        match self {
            BridgeWrapper::Http(s) => s.port(),
            BridgeWrapper::WebSocket(s) => s.port(),
        }
    }

    pub fn stop(&self) {
        match self {
            BridgeWrapper::Http(s) => s.stop(),
            BridgeWrapper::WebSocket(s) => s.stop(),
        }
    }

    pub fn get_score_info(&self) -> Option<crate::types::ScoreInfo> {
        match self {
            BridgeWrapper::Http(s) => s.get_score_info(),
            BridgeWrapper::WebSocket(s) => s.get_score_info(),
        }
    }

    pub fn queue_raw_commands(&self, cmds: Vec<serde_json::Value>) {
        match self {
            BridgeWrapper::Http(s) => s.queue_raw_commands(cmds),
            BridgeWrapper::WebSocket(s) => s.queue_raw_commands(cmds),
        }
    }

    pub fn queue_commands(&self, cmds: Vec<crate::types::AtomicCommand>) {
        match self {
            BridgeWrapper::Http(s) => s.queue_commands(cmds),
            BridgeWrapper::WebSocket(s) => s.queue_commands(cmds),
        }
    }

    pub fn server_type(&self) -> &'static str {
        match self {
            BridgeWrapper::Http(_) => "http",
            BridgeWrapper::WebSocket(_) => "websocket",
        }
    }
}

/// Application state managed by Tauri
pub struct AppState {
    bridge: Arc<RwLock<Option<BridgeWrapper>>>,
    interpreter: Arc<RwLock<LLMInterpreter>>,
    validator: CommandValidator,
    config: Arc<RwLock<Config>>,
}

impl AppState {
    pub fn new() -> Self {
        let config = Config::load();

        let interpreter = LLMInterpreter::new(
            LLMProvider::from_str(&config.provider).unwrap_or(LLMProvider::Claude),
            config.api_key.clone(),
            config.model.clone(),
        );

        Self {
            bridge: Arc::new(RwLock::new(None)),
            interpreter: Arc::new(RwLock::new(interpreter)),
            validator: CommandValidator::new(),
            config: Arc::new(RwLock::new(config)),
        }
    }
}

impl Default for AppState {
    fn default() -> Self {
        Self::new()
    }
}

/// Start the bridge server (HTTP or WebSocket based on server_type)
/// server_type: "http" for HTTP polling (port 8766), "websocket" for WebSocket (port 8765)
#[tauri::command]
pub fn start_server(state: State<AppState>, port: u16, server_type: Option<String>) -> CommandResult {
    let mut bridge_guard = state.bridge.write();

    // Stop existing server if running
    if let Some(ref bridge) = *bridge_guard {
        if bridge.is_running() {
            bridge.stop();
        }
    }

    let stype = server_type.as_deref().unwrap_or("websocket");

    match stype {
        "http" => {
            let bridge = BridgeServer::new(port);
            match bridge.start() {
                Ok(_) => {
                    info!("HTTP server started on port {}", port);
                    *bridge_guard = Some(BridgeWrapper::Http(bridge));
                    CommandResult::ok(format!("HTTP server started on port {}", port))
                }
                Err(e) => {
                    error!("Failed to start HTTP server: {}", e);
                    CommandResult::err(e)
                }
            }
        }
        "websocket" | "ws" => {
            let bridge = WsBridgeServer::new(port);
            match bridge.start() {
                Ok(_) => {
                    info!("WebSocket server started on port {}", port);
                    *bridge_guard = Some(BridgeWrapper::WebSocket(bridge));
                    CommandResult::ok(format!("WebSocket server started on port {}", port))
                }
                Err(e) => {
                    error!("Failed to start WebSocket server: {}", e);
                    CommandResult::err(e)
                }
            }
        }
        _ => CommandResult::err(format!("Unknown server type: {}. Use 'http' or 'websocket'", stype)),
    }
}

/// Stop the bridge server
#[tauri::command]
pub fn stop_server(state: State<AppState>) -> CommandResult {
    let mut bridge_guard = state.bridge.write();

    if let Some(ref bridge) = *bridge_guard {
        bridge.stop();
        info!("Server stopped");
        *bridge_guard = None;
        CommandResult::ok("Server stopped")
    } else {
        CommandResult::err("Server not running")
    }
}

/// Get the server status
#[tauri::command]
pub fn get_server_status(state: State<AppState>) -> ServerStatus {
    let bridge_guard = state.bridge.read();

    if let Some(ref bridge) = *bridge_guard {
        ServerStatus {
            running: bridge.is_running(),
            connected: bridge.is_connected(),
            port: bridge.port(),
        }
    } else {
        ServerStatus {
            running: false,
            connected: false,
            port: 8765,
        }
    }
}

/// Process a natural language request through the LLM
#[tauri::command]
pub async fn process_request(state: State<'_, AppState>, request: String) -> Result<ProcessResult, String> {
    debug!("Processing request: {}", request);

    // Get score info if available (release lock before await)
    let score_info = {
        let bridge_guard = state.bridge.read();
        bridge_guard.as_ref().and_then(|b| b.get_score_info())
    };

    // Clone interpreter data before async call (release lock before await)
    let interpreter_clone = {
        let interpreter = state.interpreter.read();
        interpreter.clone()
    };

    // Interpret the request (no locks held)
    let response = interpreter_clone
        .interpret(&request, score_info.as_ref())
        .await
        .map_err(|e| {
            error!("LLM interpretation failed: {}", e);
            e
        })?;

    debug!("LLM response: {:?}", response);

    // Validate commands
    let (valid_commands, errors) = state.validator.validate_commands(&response.commands);

    // Queue commands to the bridge
    let commands_sent = valid_commands.len();
    {
        let bridge_guard = state.bridge.read();
        if let Some(ref bridge) = *bridge_guard {
            bridge.queue_raw_commands(valid_commands);
        } else {
            return Ok(ProcessResult {
                success: false,
                intent: Some(response.intent),
                commands_sent: Some(0),
                errors: Some(vec!["Server not running".to_string()]),
                notes: response.notes,
            });
        }
    }

    Ok(ProcessResult {
        success: errors.is_empty(),
        intent: Some(response.intent),
        commands_sent: Some(commands_sent),
        errors: if errors.is_empty() {
            None
        } else {
            Some(errors)
        },
        notes: response.notes,
    })
}

/// Generate a walking bass line
#[tauri::command]
pub fn generate_bass_line(
    state: State<AppState>,
    chords: Vec<String>,
    measures: u32,
) -> CommandResult {
    if chords.is_empty() {
        return CommandResult::err("No chords provided");
    }

    // Get time signature from score info
    let time_numerator = {
        let bridge_guard = state.bridge.read();
        bridge_guard
            .as_ref()
            .and_then(|b| b.get_score_info())
            .and_then(|s| s.time_signature)
            .map(|t| t.numerator)
            .unwrap_or(4)
    };

    let generator = MusicGenerator::new(60, time_numerator);
    let commands = generator.walking_bass_line(&chords, measures, 0);

    // Queue commands
    {
        let bridge_guard = state.bridge.read();
        if let Some(ref bridge) = *bridge_guard {
            bridge.queue_commands(commands.clone());
            CommandResult::ok(format!(
                "Generated {} bass notes over {} measures",
                commands.len(),
                measures
            ))
        } else {
            CommandResult::err("Server not running")
        }
    }
}

/// Generate a drum pattern
#[tauri::command]
pub fn generate_drum_pattern(
    state: State<AppState>,
    style: String,
    measures: u32,
) -> CommandResult {
    let drum_style = DrumStyle::from_str(&style);

    // Get time signature from score info
    let time_numerator = {
        let bridge_guard = state.bridge.read();
        bridge_guard
            .as_ref()
            .and_then(|b| b.get_score_info())
            .and_then(|s| s.time_signature)
            .map(|t| t.numerator)
            .unwrap_or(4)
    };

    let generator = MusicGenerator::new(60, time_numerator);
    let commands = generator.drum_pattern(drum_style, measures, 9); // Track 9 is typically drums

    // Queue commands
    {
        let bridge_guard = state.bridge.read();
        if let Some(ref bridge) = *bridge_guard {
            bridge.queue_commands(commands.clone());
            CommandResult::ok(format!(
                "Generated {} drum hits over {} measures",
                commands.len(),
                measures
            ))
        } else {
            CommandResult::err("Server not running")
        }
    }
}

/// Configure the LLM provider
#[tauri::command]
pub fn configure_llm(
    state: State<AppState>,
    provider: String,
    api_key: String,
    model: String,
) -> CommandResult {
    let llm_provider = match LLMProvider::from_str(&provider) {
        Some(p) => p,
        None => return CommandResult::err(format!("Unknown provider: {}", provider)),
    };

    {
        let mut interpreter = state.interpreter.write();
        interpreter.set_provider(llm_provider, api_key.clone(), model.clone());
    }

    // Update config
    {
        let mut config = state.config.write();
        config.provider = provider;
        config.api_key = api_key;
        config.model = model;
    }

    info!("LLM configured");
    CommandResult::ok("LLM configured")
}

/// Get current score info
#[tauri::command]
pub fn get_score_info(state: State<AppState>) -> Option<serde_json::Value> {
    let bridge_guard = state.bridge.read();
    bridge_guard
        .as_ref()
        .and_then(|b| b.get_score_info())
        .map(|s| serde_json::to_value(s).unwrap_or_default())
}

/// Save configuration
#[tauri::command]
pub fn save_config(state: State<AppState>, config: serde_json::Value) -> CommandResult {
    let new_config: Config = match serde_json::from_value(config) {
        Ok(c) => c,
        Err(e) => return CommandResult::err(format!("Invalid config: {}", e)),
    };

    match new_config.save() {
        Ok(_) => {
            let mut current_config = state.config.write();
            *current_config = new_config;
            CommandResult::ok("Configuration saved")
        }
        Err(e) => CommandResult::err(e),
    }
}

/// Load configuration
#[tauri::command]
pub fn load_config(_state: State<AppState>) -> serde_json::Value {
    let config = Config::load();
    serde_json::to_value(config).unwrap_or_default()
}
