import { useState } from "react";
import { useAppStore } from "../lib/store";
import { startServer, stopServer, getServerStatus } from "../lib/commands";

export function ConnectionPanel() {
  const { connected, serverPort, setServerPort, setConnected, addLog } =
    useAppStore();
  const [loading, setLoading] = useState(false);
  const [serverType, setServerType] = useState<"websocket" | "http">("websocket");

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
        const result = await startServer(serverPort, serverType);
        if (result.success) {
          setConnected(true);
          addLog(`${serverType === "websocket" ? "WebSocket" : "HTTP"} server started on port ${serverPort}`);
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
    <div className="flex items-center gap-4">
      {/* Status indicator */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <div
          className={`w-2.5 h-2.5 rounded-full ${
            connected ? "bg-success animate-pulse" : "bg-error"
          }`}
        />
        <span className="text-sm text-gray-300">
          {connected ? "Connected" : "Disconnected"}
        </span>
      </div>

      {/* Server type selector */}
      <select
        className="input py-1.5 text-sm w-36"
        value={serverType}
        onChange={(e) => {
          const type = e.target.value as "websocket" | "http";
          setServerType(type);
          setServerPort(type === "websocket" ? 8765 : 8766);
        }}
        disabled={connected}
      >
        <option value="websocket">WebSocket</option>
        <option value="http">HTTP</option>
      </select>

      {/* Port input */}
      <input
        type="number"
        className="input py-1.5 text-sm w-20"
        value={serverPort}
        onChange={(e) => setServerPort(parseInt(e.target.value) || 8765)}
        disabled={connected}
        title="Server port"
      />

      {/* Buttons */}
      <div className="flex gap-2 ml-auto">
        <button
          className={`btn py-1.5 px-3 text-sm ${connected ? "btn-danger" : "btn-primary"}`}
          onClick={handleConnect}
          disabled={loading}
        >
          {loading ? "..." : connected ? "Stop" : "Start"}
        </button>
        <button
          className="btn btn-secondary py-1.5 px-2 text-sm"
          onClick={handleRefresh}
          title="Refresh status"
        >
          &#8635;
        </button>
      </div>
    </div>
  );
}
