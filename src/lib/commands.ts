import { invoke } from "@tauri-apps/api/core";

export interface ProcessResult {
  success: boolean;
  intent?: string;
  commands_sent?: number;
  errors?: string[];
  notes?: string;
}

export interface CommandResult {
  success: boolean;
  message?: string;
  error?: string;
}

// Start the bridge server
// serverType: "websocket" (default) or "http"
export async function startServer(port: number, serverType: string = "websocket"): Promise<CommandResult> {
  return await invoke("start_server", { port, serverType });
}

// Stop the bridge server
export async function stopServer(): Promise<CommandResult> {
  return await invoke("stop_server");
}

// Get server status
export async function getServerStatus(): Promise<{
  running: boolean;
  connected: boolean;
  port: number;
}> {
  return await invoke("get_server_status");
}

// Process a natural language request
export async function processRequest(
  request: string
): Promise<ProcessResult> {
  return await invoke("process_request", { request });
}

// Generate walking bass line
export async function generateBassLine(
  chords: string[],
  measures: number
): Promise<CommandResult> {
  return await invoke("generate_bass_line", { chords, measures });
}

// Generate drum pattern
export async function generateDrumPattern(
  style: string,
  measures: number
): Promise<CommandResult> {
  return await invoke("generate_drum_pattern", { style, measures });
}

// Configure LLM provider
export async function configureLLM(
  provider: string,
  apiKey: string,
  model: string
): Promise<CommandResult> {
  return await invoke("configure_llm", { provider, apiKey, model });
}

// Get current score info
export async function getScoreInfo(): Promise<object | null> {
  return await invoke("get_score_info");
}

// Request score info from the plugin
export async function requestScoreInfo(): Promise<CommandResult> {
  return await invoke("request_score_info");
}

// Save configuration
export async function saveConfig(config: object): Promise<CommandResult> {
  return await invoke("save_config", { config });
}

// Load configuration
export async function loadConfig(): Promise<object> {
  return await invoke("load_config");
}
