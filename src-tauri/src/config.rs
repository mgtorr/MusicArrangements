use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use tracing::{debug, info, warn};

/// Application configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub provider: String,
    pub api_key: String,
    pub model: String,
    #[serde(default = "default_port")]
    pub port: u16,
}

fn default_port() -> u16 {
    8766
}

impl Default for Config {
    fn default() -> Self {
        Self {
            provider: "claude".to_string(),
            api_key: String::new(),
            model: "claude-sonnet-4-20250514".to_string(),
            port: 8766,
        }
    }
}

impl Config {
    /// Get the configuration directory path
    pub fn config_dir() -> Option<PathBuf> {
        dirs::config_dir().map(|p| p.join("muse-ai-sidecar"))
    }

    /// Get the configuration file path
    pub fn config_path() -> Option<PathBuf> {
        Self::config_dir().map(|p| p.join("config.json"))
    }

    /// Load configuration from file
    pub fn load() -> Self {
        // Try to load from environment variables first
        let provider = std::env::var("LLM_PROVIDER").ok();
        let api_key = std::env::var("LLM_API_KEY").ok();
        let model = std::env::var("LLM_MODEL").ok();

        // Then try to load from config file
        let file_config = Self::load_from_file();

        // Merge: env vars take priority
        Config {
            provider: provider.unwrap_or_else(|| {
                file_config
                    .as_ref()
                    .map(|c| c.provider.clone())
                    .unwrap_or_else(|| "claude".to_string())
            }),
            api_key: api_key.unwrap_or_else(|| {
                file_config
                    .as_ref()
                    .map(|c| c.api_key.clone())
                    .unwrap_or_default()
            }),
            model: model.unwrap_or_else(|| {
                file_config
                    .as_ref()
                    .map(|c| c.model.clone())
                    .unwrap_or_else(|| "claude-sonnet-4-20250514".to_string())
            }),
            port: file_config.as_ref().map(|c| c.port).unwrap_or(8766),
        }
    }

    /// Load configuration from file only
    fn load_from_file() -> Option<Config> {
        let path = Self::config_path()?;

        if !path.exists() {
            debug!("Config file not found at {:?}", path);
            return None;
        }

        match fs::read_to_string(&path) {
            Ok(content) => match serde_json::from_str(&content) {
                Ok(config) => {
                    info!("Loaded config from {:?}", path);
                    Some(config)
                }
                Err(e) => {
                    warn!("Failed to parse config file: {}", e);
                    None
                }
            },
            Err(e) => {
                warn!("Failed to read config file: {}", e);
                None
            }
        }
    }

    /// Save configuration to file
    pub fn save(&self) -> Result<(), String> {
        let dir = Self::config_dir().ok_or("Could not determine config directory")?;
        let path = Self::config_path().ok_or("Could not determine config path")?;

        // Create directory if it doesn't exist
        if !dir.exists() {
            fs::create_dir_all(&dir)
                .map_err(|e| format!("Failed to create config directory: {}", e))?;
        }

        let content = serde_json::to_string_pretty(self)
            .map_err(|e| format!("Failed to serialize config: {}", e))?;

        fs::write(&path, content).map_err(|e| format!("Failed to write config file: {}", e))?;

        info!("Saved config to {:?}", path);
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = Config::default();
        assert_eq!(config.provider, "claude");
        assert_eq!(config.port, 8766);
    }
}
