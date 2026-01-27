import { useState, useEffect } from "react";
import { useAppStore } from "../lib/store";
import { configureLLM, saveConfig, loadConfig } from "../lib/commands";

const PROVIDERS = [
  { id: "claude", name: "Claude (Anthropic)" },
  { id: "gemini", name: "Gemini (Google)" },
  { id: "openai", name: "OpenAI" },
];

const MODELS: Record<string, string[]> = {
  claude: ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
  gemini: ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-pro"],
  openai: ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
};

export function SettingsPanel() {
  const { settingsOpen, setSettingsOpen, llmConfig, setLLMConfig, addLog } =
    useAppStore();
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    // Load config on mount
    loadConfig()
      .then((config: any) => {
        if (config) {
          setLLMConfig({
            provider: config.provider || "claude",
            apiKey: config.api_key || "",
            model: config.model || "claude-sonnet-4-20250514",
          });
        }
      })
      .catch(() => {
        // Config not found, use defaults
      });
  }, [setLLMConfig]);

  const handleSave = async () => {
    setSaving(true);
    try {
      // Configure LLM in backend
      await configureLLM(llmConfig.provider, llmConfig.apiKey, llmConfig.model);

      // Save to config file
      await saveConfig({
        provider: llmConfig.provider,
        api_key: llmConfig.apiKey,
        model: llmConfig.model,
      });

      addLog("Settings saved");
      setSettingsOpen(false);
    } catch (error) {
      addLog(`Error saving settings: ${error}`);
    }
    setSaving(false);
  };

  if (!settingsOpen) {
    return (
      <button
        className="btn btn-secondary"
        onClick={() => setSettingsOpen(true)}
      >
        Settings
      </button>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="card w-full max-w-md mx-4">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white">Settings</h2>
          <button
            className="text-gray-400 hover:text-white text-xl"
            onClick={() => setSettingsOpen(false)}
          >
            &times;
          </button>
        </div>

        <div className="space-y-4">
          {/* Provider */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">
              LLM Provider
            </label>
            <select
              className="input"
              value={llmConfig.provider}
              onChange={(e) => {
                const provider = e.target.value as typeof llmConfig.provider;
                setLLMConfig({
                  provider,
                  model: MODELS[provider][0],
                });
              }}
            >
              {PROVIDERS.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          {/* Model */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">Model</label>
            <select
              className="input"
              value={llmConfig.model}
              onChange={(e) => setLLMConfig({ model: e.target.value })}
            >
              {MODELS[llmConfig.provider].map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>

          {/* API Key */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">API Key</label>
            <input
              type="password"
              className="input"
              value={llmConfig.apiKey}
              onChange={(e) => setLLMConfig({ apiKey: e.target.value })}
              placeholder="Enter your API key"
            />
            <p className="text-xs text-gray-500 mt-1">
              {llmConfig.provider === "claude" &&
                "Get your key from console.anthropic.com"}
              {llmConfig.provider === "gemini" &&
                "Get your key from makersuite.google.com"}
              {llmConfig.provider === "openai" &&
                "Get your key from platform.openai.com"}
            </p>
          </div>
        </div>

        <div className="flex gap-2 mt-6">
          <button
            className="btn btn-secondary flex-1"
            onClick={() => setSettingsOpen(false)}
          >
            Cancel
          </button>
          <button
            className="btn btn-primary flex-1"
            onClick={handleSave}
            disabled={saving || !llmConfig.apiKey}
          >
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
