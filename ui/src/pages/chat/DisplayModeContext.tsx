import { createContext, useContext, useState, ReactNode } from "react";
import type { DisplayMode } from "./types";

interface DisplayModeContextType {
  mode: DisplayMode;
  setMode: (mode: DisplayMode) => void;
}

const DisplayModeContext = createContext<DisplayModeContextType | undefined>(undefined);

export function DisplayModeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<DisplayMode>(() => {
    try {
      const stored = localStorage.getItem("browser-mcp-display-mode");
      if (stored === "advanced") return "developer";
      return (stored as DisplayMode) || "simple";
    } catch {
      return "simple";
    }
  });

  const handleSetMode = (newMode: DisplayMode) => {
    setMode(newMode);
    try {
      localStorage.setItem("browser-mcp-display-mode", newMode);
    } catch {}
  };

  return (
    <DisplayModeContext.Provider value={{ mode, setMode: handleSetMode }}>
      {children}
    </DisplayModeContext.Provider>
  );
}

export function useDisplayMode() {
  const context = useContext(DisplayModeContext);
  if (!context) {
    throw new Error("useDisplayMode must be used within a DisplayModeProvider");
  }
  return context;
}
