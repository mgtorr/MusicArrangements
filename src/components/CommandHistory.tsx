import { useAppStore } from "../lib/store";
import { useRef, useEffect } from "react";

export function CommandHistory() {
  const { logs, clearLogs } = useAppStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-2 border-b border-gray-700">
        <h2 className="text-sm font-semibold text-white">Command History</h2>
        <button
          onClick={clearLogs}
          className="text-xs text-gray-400 hover:text-white transition-colors"
          title="Clear history"
        >
          Clear
        </button>
      </div>

      {/* Log entries */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-3 space-y-1 font-mono text-xs"
      >
        {logs.length === 0 ? (
          <p className="text-gray-500 text-center py-4">
            No commands executed yet
          </p>
        ) : (
          logs.map((log, index) => (
            <div
              key={index}
              className={`py-1 px-2 rounded ${
                log.includes("Error")
                  ? "bg-red-900/20 text-red-400"
                  : log.includes("success") || log.includes("Connected")
                  ? "bg-green-900/20 text-green-400"
                  : "text-gray-400"
              }`}
            >
              {log}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
