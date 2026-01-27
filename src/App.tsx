import { useEffect } from "react";
import { ConnectionPanel } from "./components/ConnectionPanel";
import { ScoreInfo } from "./components/ScoreInfo";
import { ChatPanel } from "./components/ChatPanel";
import { LogPanel } from "./components/LogPanel";
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
    <div className="min-h-screen bg-surface p-4 flex flex-col gap-4">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-accent flex items-center justify-center">
            <span className="text-xl">&#9835;</span>
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Muse AI Sidecar</h1>
            <p className="text-xs text-gray-400">AI-powered music arrangement</p>
          </div>
        </div>
        <SettingsPanel />
      </header>

      {/* Main content */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left column - Connection and Score Info */}
        <div className="flex flex-col gap-4">
          <ConnectionPanel />
          <ScoreInfo />
        </div>

        {/* Center column - Chat */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <ChatPanel />
          <LogPanel />
        </div>
      </div>
    </div>
  );
}

export default App;
