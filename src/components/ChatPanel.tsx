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
    <div className="card flex-1 flex flex-col min-h-[300px]">
      <h2 className="text-lg font-semibold text-white mb-4">Chat</h2>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto space-y-3 mb-4 pr-2">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <p className="mb-2">Start by describing what you want to do:</p>
            <p className="text-sm text-gray-600">
              "Add a C major chord at the beginning"
            </p>
            <p className="text-sm text-gray-600">"Add a piano part with arpeggios"</p>
            <p className="text-sm text-gray-600 mt-4">
              Or use commands: /bass C G Am F 4, /drums rock 4
            </p>
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
                className={`max-w-[80%] rounded-lg px-4 py-2 ${
                  message.role === "user"
                    ? "bg-accent text-white"
                    : "bg-surface-hover text-gray-200"
                }`}
              >
                <p className="text-sm">{message.content}</p>
                {message.commands !== undefined && message.commands > 0 && (
                  <p className="text-xs text-gray-400 mt-1">
                    {message.commands} command(s) sent
                  </p>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input form */}
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
          className="btn btn-primary"
          disabled={!connected || loading || !input.trim()}
        >
          {loading ? "..." : "Send"}
        </button>
      </form>
    </div>
  );
}
