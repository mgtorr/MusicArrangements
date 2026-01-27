import { create } from "zustand";

export interface ScoreInfo {
  title: string;
  composer: string;
  measures: number;
  staves: number;
  parts: { name: string }[];
  timeSignature: { numerator: number; denominator: number };
  keySignature: number;
  tempo: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  commands?: number;
}

export interface LLMConfig {
  provider: "claude" | "gemini" | "openai";
  apiKey: string;
  model: string;
}

interface AppState {
  // Connection state
  connected: boolean;
  serverPort: number;
  setConnected: (connected: boolean) => void;
  setServerPort: (port: number) => void;

  // Score info
  scoreInfo: ScoreInfo | null;
  setScoreInfo: (info: ScoreInfo | null) => void;

  // Chat messages
  messages: Message[];
  addMessage: (message: Omit<Message, "id" | "timestamp">) => void;
  clearMessages: () => void;

  // Logs
  logs: string[];
  addLog: (log: string) => void;
  clearLogs: () => void;

  // LLM configuration
  llmConfig: LLMConfig;
  setLLMConfig: (config: Partial<LLMConfig>) => void;

  // Settings panel
  settingsOpen: boolean;
  setSettingsOpen: (open: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Connection state
  connected: false,
  serverPort: 8766,
  setConnected: (connected) => set({ connected }),
  setServerPort: (serverPort) => set({ serverPort }),

  // Score info
  scoreInfo: null,
  setScoreInfo: (scoreInfo) => set({ scoreInfo }),

  // Chat messages
  messages: [],
  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: crypto.randomUUID(),
          timestamp: new Date(),
        },
      ],
    })),
  clearMessages: () => set({ messages: [] }),

  // Logs
  logs: [],
  addLog: (log) =>
    set((state) => ({
      logs: [...state.logs, `[${new Date().toLocaleTimeString()}] ${log}`],
    })),
  clearLogs: () => set({ logs: [] }),

  // LLM configuration
  llmConfig: {
    provider: "claude",
    apiKey: "",
    model: "claude-sonnet-4-20250514",
  },
  setLLMConfig: (config) =>
    set((state) => ({
      llmConfig: { ...state.llmConfig, ...config },
    })),

  // Settings panel
  settingsOpen: false,
  setSettingsOpen: (settingsOpen) => set({ settingsOpen }),
}));
