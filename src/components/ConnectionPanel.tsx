import { useState } from "react";
import { useAppStore } from "../lib/store";
import { startServer, stopServer, getServerStatus } from "../lib/commands";

export function ConnectionPanel() {
  const { connected, serverPort, setServerPort, setConnected, addLog } =
    useAppStore();
  const [loading, setLoading] = useState(false);

  const handleConnect = async () => {
    setLoading(true);
    try {
      if (connected) {
        const result = await stopServer();
        if (result.success) {
          setConnected(false);
          addLog("Server stopped");
        } else {
          addLog(`Error: ${result.error}`);
        }
      } else {
        const result = await startServer(serverPort);
        if (result.success) {
          setConnected(true);
          addLog(`Server started on port ${serverPort}`);
        } else {
          addLog(`Error: ${result.error}`);
        }
      }
    } catch (error) {
      addLog(`Error: ${error}`);
    }
    setLoading(false);
  };

  const handleRefresh = async () => {
    try {
      const status = await getServerStatus();
      setConnected(status.connected);
      addLog(`Status: ${status.running ? "Running" : "Stopped"}, Plugin: ${status.connected ? "Connected" : "Disconnected"}`);
    } catch (error) {
      addLog(`Error checking status: ${error}`);
    }
  };

  return (
    <div className="card">
      <h2 className="text-lg font-semibold text-white mb-4">Connection</h2>

      <div className="space-y-4">
        {/* Status indicator */}
        <div className="flex items-center gap-2">
          <div
            className={`w-3 h-3 rounded-full ${
              connected ? "bg-success" : "bg-error"
            }`}
          />
          <span className="text-sm text-gray-300">
            {connected ? "Connected to MuseScore" : "Disconnected"}
          </span>
        </div>

        {/* Port input */}
        <div>
          <label className="block text-sm text-gray-400 mb-1">
            Server Port
          </label>
          <input
            type="number"
            className="input"
            value={serverPort}
            onChange={(e) => setServerPort(parseInt(e.target.value) || 8766)}
            disabled={connected}
          />
        </div>

        {/* Buttons */}
        <div className="flex gap-2">
          <button
            className={`btn flex-1 ${connected ? "btn-danger" : "btn-primary"}`}
            onClick={handleConnect}
            disabled={loading}
          >
            {loading
              ? "..."
              : connected
              ? "Stop Server"
              : "Start Server"}
          </button>
          <button
            className="btn btn-secondary"
            onClick={handleRefresh}
            title="Refresh status"
          >
            &#8635;
          </button>
        </div>

        {/* Instructions */}
        <p className="text-xs text-gray-500">
          Start the server, then connect from MuseScore using the LLM Bridge
          plugin.
        </p>
      </div>
    </div>
  );
}
