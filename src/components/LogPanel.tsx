import { useRef, useEffect } from "react";
import { useAppStore } from "../lib/store";

export function LogPanel() {
  const { logs, clearLogs } = useAppStore();
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-lg font-semibold text-white">Log</h2>
        <button
          className="text-xs text-gray-400 hover:text-white"
          onClick={clearLogs}
        >
          Clear
        </button>
      </div>

      <div className="bg-surface rounded-lg p-3 h-32 overflow-y-auto font-mono text-xs">
        {logs.length === 0 ? (
          <span className="text-gray-500">No logs yet</span>
        ) : (
          logs.map((log, index) => (
            <div key={index} className="text-green-400">
              {log}
            </div>
          ))
        )}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
}
