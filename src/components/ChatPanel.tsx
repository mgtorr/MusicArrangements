import { useState, useRef, useEffect } from "react";
import { useAppStore } from "../lib/store";
import {
  processRequest,
  generateBassLine,
  generateDrumPattern,
} from "../lib/commands";

export function ChatPanel() {
  const { messages, addMessage, connected, addLog } = useAppStore();
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput("");

    // Check for special commands
    if (userMessage.startsWith("/bass ")) {
      await handleBassCommand(userMessage.slice(6));
      return;
    }
    if (userMessage.startsWith("/drums ")) {
      await handleDrumsCommand(userMessage.slice(7));
      return;
    }

    addMessage({ role: "user", content: userMessage });
    setLoading(true);

    try {
      const result = await processRequest(userMessage);
      if (result.success) {
        addMessage({
          role: "assistant",
          content: result.intent || "Request processed",
          commands: result.commands_sent,
        });
        if (result.notes) {
          addLog(`Notes: ${result.notes}`);
        }
        if (result.errors && result.errors.length > 0) {
          result.errors.forEach((err) => addLog(`Error: ${err}`));
        }
      } else {
        addMessage({
          role: "assistant",
          content: `Error: ${result.errors?.join(", ") || "Unknown error"}`,
        });
      }
    } catch (error) {
      addMessage({
        role: "assistant",
        content: `Error: ${error}`,
      });
    }

    setLoading(false);
  };

  const handleBassCommand = async (args: string) => {
    const parts = args.split(" ");
    const measures = parseInt(parts.pop() || "4");
    const chords = parts;

    if (chords.length === 0) {
      addMessage({
        role: "assistant",
        content: "Usage: /bass C G Am F 4 (chords followed by number of measures)",
      });
      return;
    }

    addMessage({ role: "user", content: `/bass ${args}` });
    setLoading(true);

    try {
      const result = await generateBassLine(chords, measures);
      addMessage({
        role: "assistant",
        content: result.success
          ? `Generated walking bass line for ${chords.join("-")} over ${measures} measures`
          : `Error: ${result.error}`,
      });
    } catch (error) {
      addMessage({ role: "assistant", content: `Error: ${error}` });
    }

    setLoading(false);
  };

  const handleDrumsCommand = async (args: string) => {
    const [style, measuresStr] = args.split(" ");
    const measures = parseInt(measuresStr || "4");

    addMessage({ role: "user", content: `/drums ${args}` });
    setLoading(true);

    try {
      const result = await generateDrumPattern(style || "rock", measures);
      addMessage({
        role: "assistant",
        content: result.success
          ? `Generated ${style || "rock"} drum pattern for ${measures} measures`
          : `Error: ${result.error}`,
      });
    } catch (error) {
      addMessage({ role: "assistant", content: `Error: ${error}` });
    }

    setLoading(false);
  };

  return (
    <div className="h-full flex flex-col">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-surface-hover flex items-center justify-center">
              <span className="text-2xl">&#9835;</span>
            </div>
            <p className="mb-3 text-gray-400">Start by describing what you want to do:</p>
            <div className="space-y-2 text-sm">
              <p className="text-gray-500">"Add a C major chord at the beginning"</p>
              <p className="text-gray-500">"Add a piano part with arpeggios"</p>
              <p className="text-gray-500">"Transpose the melody up a fifth"</p>
            </div>
            <div className="mt-6 pt-4 border-t border-gray-700">
              <p className="text-xs text-gray-600 mb-2">Quick commands:</p>
              <div className="flex flex-wrap justify-center gap-2">
                <code className="text-xs bg-surface-hover px-2 py-1 rounded text-gray-400">/bass C G Am F 4</code>
                <code className="text-xs bg-surface-hover px-2 py-1 rounded text-gray-400">/drums rock 4</code>
              </div>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[85%] rounded-xl px-4 py-2.5 ${
                  message.role === "user"
                    ? "bg-accent text-white rounded-br-sm"
                    : "bg-surface-hover text-gray-200 rounded-bl-sm"
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                {message.commands !== undefined && message.commands > 0 && (
                  <p className="text-xs opacity-70 mt-1.5 flex items-center gap-1">
                    <span>&#10003;</span>
                    {message.commands} command{message.commands > 1 ? "s" : ""} sent
                  </p>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input form */}
      <div className="flex-shrink-0 p-3 border-t border-gray-700 bg-surface">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            className="input flex-1"
            placeholder={
              connected
                ? "Describe what you want to add to the score..."
                : "Connect to MuseScore first..."
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={!connected || loading}
          />
          <button
            type="submit"
            className="btn btn-primary px-4"
            disabled={!connected || loading || !input.trim()}
          >
            {loading ? (
              <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            ) : (
              <span>&#10148;</span>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
