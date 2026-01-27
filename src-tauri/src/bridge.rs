use crate::types::{AtomicCommand, ScoreInfo};
use parking_lot::RwLock;
use serde_json::json;
use std::collections::VecDeque;
use std::io::{BufRead, BufReader, Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Instant;
use tracing::{debug, error, info, warn};

/// Bridge server for communicating with MuseScore plugin
pub struct BridgeServer {
    port: u16,
    running: Arc<AtomicBool>,
    connected: Arc<AtomicBool>,
    pending_commands: Arc<RwLock<VecDeque<serde_json::Value>>>,
    score_info: Arc<RwLock<Option<ScoreInfo>>>,
    last_ping: Arc<RwLock<Option<Instant>>>,
}

impl BridgeServer {
    pub fn new(port: u16) -> Self {
        Self {
            port,
            running: Arc::new(AtomicBool::new(false)),
            connected: Arc::new(AtomicBool::new(false)),
            pending_commands: Arc::new(RwLock::new(VecDeque::new())),
            score_info: Arc::new(RwLock::new(None)),
            last_ping: Arc::new(RwLock::new(None)),
        }
    }

    /// Start the HTTP server
    pub fn start(&self) -> Result<(), String> {
        if self.running.load(Ordering::SeqCst) {
            return Err("Server already running".to_string());
        }

        let listener = TcpListener::bind(format!("127.0.0.1:{}", self.port))
            .map_err(|e| format!("Failed to bind to port {}: {}", self.port, e))?;

        listener
            .set_nonblocking(true)
            .map_err(|e| format!("Failed to set non-blocking: {}", e))?;

        self.running.store(true, Ordering::SeqCst);
        info!("Bridge server started on port {}", self.port);

        let running = self.running.clone();
        let connected = self.connected.clone();
        let pending_commands = self.pending_commands.clone();
        let score_info = self.score_info.clone();
        let last_ping = self.last_ping.clone();

        thread::spawn(move || {
            while running.load(Ordering::SeqCst) {
                match listener.accept() {
                    Ok((stream, _)) => {
                        let connected = connected.clone();
                        let pending_commands = pending_commands.clone();
                        let score_info = score_info.clone();
                        let last_ping = last_ping.clone();

                        thread::spawn(move || {
                            if let Err(e) = handle_connection(
                                stream,
                                &connected,
                                &pending_commands,
                                &score_info,
                                &last_ping,
                            ) {
                                debug!("Connection error: {}", e);
                            }
                        });
                    }
                    Err(ref e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                        thread::sleep(std::time::Duration::from_millis(50));
                    }
                    Err(e) => {
                        error!("Accept error: {}", e);
                    }
                }

                // Check for connection timeout (5 seconds without ping)
                if let Some(last) = *last_ping.read() {
                    if last.elapsed().as_secs() > 5 {
                        if connected.load(Ordering::SeqCst) {
                            info!("Plugin connection timed out");
                            connected.store(false, Ordering::SeqCst);
                        }
                    }
                }
            }
            info!("Bridge server stopped");
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
    }

    /// Queue multiple commands
    pub fn queue_commands(&self, cmds: Vec<AtomicCommand>) {
        let mut commands = self.pending_commands.write();
        for cmd in cmds {
            commands.push_back(cmd.to_json());
        }
    }

    /// Queue raw JSON commands
    pub fn queue_raw_commands(&self, cmds: Vec<serde_json::Value>) {
        let mut commands = self.pending_commands.write();
        for cmd in cmds {
            commands.push_back(cmd);
        }
    }

    /// Get the current score info
    pub fn get_score_info(&self) -> Option<ScoreInfo> {
        self.score_info.read().clone()
    }
}

fn handle_connection(
    mut stream: TcpStream,
    connected: &Arc<AtomicBool>,
    pending_commands: &Arc<RwLock<VecDeque<serde_json::Value>>>,
    score_info: &Arc<RwLock<Option<ScoreInfo>>>,
    last_ping: &Arc<RwLock<Option<Instant>>>,
) -> Result<(), String> {
    stream
        .set_read_timeout(Some(std::time::Duration::from_secs(5)))
        .map_err(|e| e.to_string())?;

    let reader_stream = stream.try_clone().map_err(|e| e.to_string())?;
    let mut reader = BufReader::new(reader_stream);
    let mut request_line = String::new();
    reader
        .read_line(&mut request_line)
        .map_err(|e| e.to_string())?;

    let parts: Vec<&str> = request_line.trim().split_whitespace().collect();
    if parts.len() < 2 {
        return Err("Invalid request".to_string());
    }

    let method = parts[0];
    let path = parts[1];

    // Read headers
    let mut content_length: usize = 0;
    loop {
        let mut header = String::new();
        reader.read_line(&mut header).map_err(|e| e.to_string())?;
        if header.trim().is_empty() {
            break;
        }
        if header.to_lowercase().starts_with("content-length:") {
            content_length = header
                .split(':')
                .nth(1)
                .and_then(|s| s.trim().parse().ok())
                .unwrap_or(0);
        }
    }

    // Read body if present
    let body = if content_length > 0 {
        let mut body = vec![0u8; content_length];
        reader
            .read_exact(&mut body)
            .map_err(|e: std::io::Error| e.to_string())?;
        Some(String::from_utf8_lossy(&body).to_string())
    } else {
        None
    };

    // Route request
    let response = match (method, path) {
        ("GET", "/ping") => {
            connected.store(true, Ordering::SeqCst);
            *last_ping.write() = Some(Instant::now());
            json!({
                "status": "ok",
                "version": "1.0.0"
            })
        }
        ("GET", "/poll") => {
            *last_ping.write() = Some(Instant::now());
            let mut commands = pending_commands.write();
            let cmds: Vec<_> = commands.drain(..).collect();
            json!({
                "commands": cmds
            })
        }
        ("POST", "/score_info") => {
            if let Some(body) = body {
                match serde_json::from_str::<ScoreInfo>(&body) {
                    Ok(info) => {
                        debug!("Received score info: {:?}", info);
                        *score_info.write() = Some(info);
                        json!({ "status": "ok" })
                    }
                    Err(e) => {
                        warn!("Failed to parse score info: {}", e);
                        json!({ "status": "error", "message": e.to_string() })
                    }
                }
            } else {
                json!({ "status": "error", "message": "No body" })
            }
        }
        ("POST", "/results") => {
            if let Some(body) = body {
                debug!("Received results: {}", body);
            }
            json!({ "status": "ok" })
        }
        _ => {
            json!({ "status": "error", "message": "Not found" })
        }
    };

    // Send response
    let response_body = serde_json::to_string(&response).unwrap_or_default();
    let http_response = format!(
        "HTTP/1.1 200 OK\r\n\
         Content-Type: application/json\r\n\
         Content-Length: {}\r\n\
         Access-Control-Allow-Origin: *\r\n\
         Connection: close\r\n\
         \r\n\
         {}",
        response_body.len(),
        response_body
    );

    stream
        .write_all(http_response.as_bytes())
        .map_err(|e| e.to_string())?;
    stream.flush().map_err(|e| e.to_string())?;

    Ok(())
}
