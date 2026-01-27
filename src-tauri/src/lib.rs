mod bridge;
mod commands;
mod config;
mod llm;
mod music;
mod types;
mod validator;
mod ws_bridge;

use tauri::Manager;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

pub fn run() {
    // Initialize logging
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "muse_ai_sidecar=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // Initialize the app state
            let state = commands::AppState::new();
            app.manage(state);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::start_server,
            commands::stop_server,
            commands::get_server_status,
            commands::process_request,
            commands::generate_bass_line,
            commands::generate_drum_pattern,
            commands::configure_llm,
            commands::get_score_info,
            commands::save_config,
            commands::load_config,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
