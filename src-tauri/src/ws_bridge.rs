use crate::types::{AtomicCommand, ScoreInfo};
use futures_util::{SinkExt, StreamExt};
use parking_lot::RwLock;
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::collections::VecDeque;
use std::net::SocketAddr;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::broadcast;
use tokio_tungstenite::{accept_async, tungstenite::Message};
use tracing::{debug, error, info, warn};

/// WebSocket message types
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum WsMessage {
    // Client -> Server
    Ping { timestamp: u64 },
    ScoreInfo(ScoreInfo),
    Result {
        command: String,
        success: bool,
        error: Option<String>,
        #[serde(rename = "commandId")]
        command_id: Option<String>,
    },

    // Server -> Client
    Pong { timestamp: u64 },
    Command { command: serde_json::Value },
    Commands { commands: Vec<serde_json::Value> },
    RequestScoreInfo,
    Error { message: String },
}

/// WebSocket bridge server for MuseScore plugin communication
pub struct WsBridgeServer {
    port: u16,
    running: Arc<AtomicBool>,
    connected: Arc<AtomicBool>,
    pending_commands: Arc<RwLock<VecDeque<serde_json::Value>>>,
    score_info: Arc<RwLock<Option<ScoreInfo>>>,
    tx: broadcast::Sender<String>,
}

impl WsBridgeServer {
    pub fn new(port: u16) -> Self {
        let (tx, _) = broadcast::channel(100);
        Self {
            port,
            running: Arc::new(AtomicBool::new(false)),
            connected: Arc::new(AtomicBool::new(false)),
            pending_commands: Arc::new(RwLock::new(VecDeque::new())),
            score_info: Arc::new(RwLock::new(None)),
            tx,
        }
    }

    /// Start the WebSocket server
    pub fn start(&self) -> Result<(), String> {
        if self.running.load(Ordering::SeqCst) {
            return Err("Server already running".to_string());
        }

        let addr: SocketAddr = format!("127.0.0.1:{}", self.port)
            .parse()
            .map_err(|e| format!("Invalid address: {}", e))?;

        self.running.store(true, Ordering::SeqCst);

        let running = self.running.clone();
        let connected = self.connected.clone();
        let pending_commands = self.pending_commands.clone();
        let score_info = self.score_info.clone();
        let tx = self.tx.clone();
        let port = self.port;

        // Spawn the server in a tokio task
        tokio::spawn(async move {
            match TcpListener::bind(&addr).await {
                Ok(listener) => {
                    info!("WebSocket server started on port {}", port);

                    while running.load(Ordering::SeqCst) {
                        tokio::select! {
                            result = listener.accept() => {
                                match result {
                                    Ok((stream, peer_addr)) => {
                                        info!("New connection from: {}", peer_addr);

                                        let running = running.clone();
                                        let connected = connected.clone();
                                        let pending_commands = pending_commands.clone();
                                        let score_info = score_info.clone();
                                        let mut rx = tx.subscribe();

                                        tokio::spawn(async move {
                                            if let Err(e) = handle_connection(
                                                stream,
                                                &running,
                                                &connected,
                                                &pending_commands,
                                                &score_info,
                                                &mut rx,
                                            ).await {
                                                debug!("Connection error: {}", e);
                                            }
                                            connected.store(false, Ordering::SeqCst);
                                            info!("Client disconnected: {}", peer_addr);
                                        });
                                    }
                                    Err(e) => {
                                        error!("Accept error: {}", e);
                                    }
                                }
                            }
                            _ = tokio::time::sleep(tokio::time::Duration::from_millis(100)) => {
                                // Check if we should stop
                                if !running.load(Ordering::SeqCst) {
                                    break;
                                }
                            }
                        }
                    }

                    info!("WebSocket server stopped");
                }
                Err(e) => {
                    error!("Failed to bind WebSocket server: {}", e);
                    running.store(false, Ordering::SeqCst);
                }
            }
        });

        Ok(())
    }

    /// Stop the server
    pub fn stop(&self) {
        self.running.store(false, Ordering::SeqCst);
        self.connected.store(false, Ordering::SeqCst);
    }

    /// Check if server is running
    pub fn is_running(&self) -> bool {
        self.running.load(Ordering::SeqCst)
    }

    /// Check if plugin is connected
    pub fn is_connected(&self) -> bool {
        self.connected.load(Ordering::SeqCst)
    }

    /// Get the server port
    pub fn port(&self) -> u16 {
        self.port
    }

    /// Queue a command to send to the plugin
    pub fn queue_command(&self, command: AtomicCommand) {
        let mut commands = self.pending_commands.write();
        commands.push_back(command.to_json());
        // Broadcast to connected client
        let msg = json!({
            "type": "command",
            "command": command.to_json()
        });
        let _ = self.tx.send(msg.to_string());
    }

    /// Queue multiple commands
    pub fn queue_commands(&self, cmds: Vec<AtomicCommand>) {
        let json_cmds: Vec<_> = cmds.iter().map(|c| c.to_json()).collect();
        {
            let mut commands = self.pending_commands.write();
            for cmd in &json_cmds {
                commands.push_back(cmd.clone());
            }
        }
        // Broadcast to connected client
        let msg = json!({
            "type": "commands",
            "commands": json_cmds
        });
        let _ = self.tx.send(msg.to_string());
    }

    /// Queue raw JSON commands
    pub fn queue_raw_commands(&self, cmds: Vec<serde_json::Value>) {
        {
            let mut commands = self.pending_commands.write();
            for cmd in &cmds {
                commands.push_back(cmd.clone());
            }
        }
        // Broadcast to connected client
        let msg = json!({
            "type": "commands",
            "commands": cmds
        });
        let _ = self.tx.send(msg.to_string());
    }

    /// Get the current score info
    pub fn get_score_info(&self) -> Option<ScoreInfo> {
        self.score_info.read().clone()
    }

    /// Request score info from plugin
    pub fn request_score_info(&self) {
        let msg = json!({ "type": "request_score_info" });
        let _ = self.tx.send(msg.to_string());
    }
}

async fn handle_connection(
    stream: TcpStream,
    running: &Arc<AtomicBool>,
    connected: &Arc<AtomicBool>,
    pending_commands: &Arc<RwLock<VecDeque<serde_json::Value>>>,
    score_info: &Arc<RwLock<Option<ScoreInfo>>>,
    rx: &mut broadcast::Receiver<String>,
) -> Result<(), String> {
    let ws_stream = accept_async(stream)
        .await
        .map_err(|e| format!("WebSocket handshake failed: {}", e))?;

    connected.store(true, Ordering::SeqCst);
    info!("WebSocket connection established");

    let (mut write, mut read) = ws_stream.split();

    // Send any pending commands immediately (release lock before await)
    let pending_msg = {
        let mut commands = pending_commands.write();
        if !commands.is_empty() {
            let cmds: Vec<_> = commands.drain(..).collect();
            Some(json!({
                "type": "commands",
                "commands": cmds
            }).to_string())
        } else {
            None
        }
    };
    if let Some(msg) = pending_msg {
        if let Err(e) = write.send(Message::Text(msg)).await {
            warn!("Failed to send pending commands: {}", e);
        }
    }

    loop {
        if !running.load(Ordering::SeqCst) {
            break;
        }

        tokio::select! {
            // Handle incoming messages from plugin
            msg = read.next() => {
                match msg {
                    Some(Ok(Message::Text(text))) => {
                        if let Err(e) = handle_plugin_message(&text, &mut write, score_info).await {
                            warn!("Error handling message: {}", e);
                        }
                    }
                    Some(Ok(Message::Close(_))) => {
                        info!("Client initiated close");
                        break;
                    }
                    Some(Ok(Message::Ping(data))) => {
                        let _ = write.send(Message::Pong(data)).await;
                    }
                    Some(Err(e)) => {
                        error!("WebSocket error: {}", e);
                        break;
                    }
                    None => {
                        debug!("WebSocket stream ended");
                        break;
                    }
                    _ => {}
                }
            }

            // Handle outgoing messages to plugin (from broadcast channel)
            msg = rx.recv() => {
                match msg {
                    Ok(text) => {
                        if let Err(e) = write.send(Message::Text(text)).await {
                            warn!("Failed to send message: {}", e);
                            break;
                        }
                    }
                    Err(broadcast::error::RecvError::Lagged(n)) => {
                        warn!("Skipped {} messages", n);
                    }
                    Err(broadcast::error::RecvError::Closed) => {
                        break;
                    }
                }
            }

            // Timeout to check if we should stop
            _ = tokio::time::sleep(tokio::time::Duration::from_millis(100)) => {
                // Just continue the loop to check running flag
            }
        }
    }

    connected.store(false, Ordering::SeqCst);
    Ok(())
}

async fn handle_plugin_message(
    text: &str,
    write: &mut futures_util::stream::SplitSink<
        tokio_tungstenite::WebSocketStream<TcpStream>,
        Message,
    >,
    score_info: &Arc<RwLock<Option<ScoreInfo>>>,
) -> Result<(), String> {
    let msg: serde_json::Value =
        serde_json::from_str(text).map_err(|e| format!("JSON parse error: {}", e))?;

    let msg_type = msg["type"].as_str().unwrap_or("");

    match msg_type {
        "ping" => {
            let timestamp = msg["timestamp"].as_u64().unwrap_or(0);
            let response = json!({ "type": "pong", "timestamp": timestamp });
            write
                .send(Message::Text(response.to_string()))
                .await
                .map_err(|e| e.to_string())?;
        }
        "score_info" => {
            // Parse and store score info
            if let Ok(info) = serde_json::from_value::<ScoreInfo>(msg.clone()) {
                debug!("Received score info: {:?}", info);
                *score_info.write() = Some(info);
            } else if msg.get("error").is_some() {
                warn!("Score info error: {:?}", msg["error"]);
            }
        }
        "result" => {
            let command = msg["command"].as_str().unwrap_or("unknown");
            let success = msg["success"].as_bool().unwrap_or(false);
            if success {
                debug!("Command '{}' executed successfully", command);
            } else {
                let error = msg["error"].as_str().unwrap_or("Unknown error");
                warn!("Command '{}' failed: {}", command, error);
            }
        }
        _ => {
            debug!("Unknown message type: {}", msg_type);
        }
    }

    Ok(())
}
