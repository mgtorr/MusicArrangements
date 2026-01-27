import { useEffect } from "react";
import { ConnectionPanel } from "./components/ConnectionPanel";
import { ScoreInfo } from "./components/ScoreInfo";
import { ChatPanel } from "./components/ChatPanel";
import { CommandHistory } from "./components/CommandHistory";
import { SettingsPanel } from "./components/SettingsPanel";
import { useAppStore } from "./lib/store";
import { listen } from "@tauri-apps/api/event";

function App() {
  const { addLog, setConnected, setScoreInfo } = useAppStore();

  useEffect(() => {
    // Listen for events from the Rust backend
    const unlisten = Promise.all([
      listen<string>("log", (event) => {
        addLog(event.payload);
      }),
      listen<boolean>("connection-status", (event) => {
        setConnected(event.payload);
      }),
      listen<object>("score-info", (event) => {
        setScoreInfo(event.payload as any);
      }),
    ]);

    return () => {
      unlisten.then((unlisteners) => {
        unlisteners.forEach((fn) => fn());
      });
    };
  }, [addLog, setConnected, setScoreInfo]);

  return (
    <div className="h-screen bg-surface flex flex-col overflow-hidden">
      {/* Header */}
      <header className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b border-gray-700 bg-surface-elevated">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-accent to-purple-600 flex items-center justify-center shadow-lg">
            <span className="text-lg">&#9835;</span>
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">Muse AI Sidecar</h1>
            <p className="text-xs text-gray-500">AI-powered music arrangement</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <SettingsPanel />
        </div>
      </header>

      {/* Main content - Two column layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Chat */}
        <div className="w-1/2 flex flex-col border-r border-gray-700">
          {/* Connection status bar */}
          <div className="flex-shrink-0 p-3 border-b border-gray-700 bg-surface">
            <ConnectionPanel />
          </div>

          {/* Chat area */}
          <div className="flex-1 overflow-hidden">
            <ChatPanel />
          </div>
        </div>

        {/* Right Panel - Score Preview & Command History */}
        <div className="w-1/2 flex flex-col bg-surface">
          {/* Score Info */}
          <div className="flex-shrink-0 p-3 border-b border-gray-700">
            <ScoreInfo />
          </div>

          {/* Command History */}
          <div className="flex-1 overflow-hidden">
            <CommandHistory />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
