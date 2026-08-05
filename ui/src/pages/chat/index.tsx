import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { getChatConfig } from "../../services/chat";
import { useChat } from "./useChat";
import { ChatToolbar } from "./ChatToolbar";
import { ChatThread } from "./ChatThread";
import { ChatComposer } from "./ChatComposer";
import { SettingsDrawer } from "./SettingsDrawer";
import { DisplayModeProvider } from "./DisplayModeContext";

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean }> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() { return { hasError: true }; }
  render() {
    if (this.state.hasError) {
      return (
        <div className="state slide-up" style={{ marginTop: "10vh" }}>
          <div className="state-title">Something went wrong</div>
          <div className="state-sub">A rendering error occurred in the chat UI.</div>
          <button className="btn btn-primary" onClick={() => window.location.reload()} style={{marginTop:"1rem"}}>Reload Page</button>
        </div>
      );
    }
    return this.props.children;
  }
}
import React from "react";

export function ChatPage() {
  const { data: config, isLoading: loadingConfig, error: configError } = useQuery({
    queryKey: ["chat-config"],
    queryFn: getChatConfig,
  });

  const [model, setModel] = useState<string | undefined>(undefined);
  const [input, setInput] = useState("");
  const [drawerOpen, setDrawerOpen] = useState(() => {
     try {
        return localStorage.getItem("browser-mcp-drawer-open") !== "false";
     } catch { return true; }
  });

  useEffect(() => {
     try { localStorage.setItem("browser-mcp-drawer-open", String(drawerOpen)); } catch {}
  }, [drawerOpen]);

  const activeModel = model ?? config?.model ?? "";
  const { turns, busy, send, stop } = useChat(activeModel);

  if (loadingConfig) {
    return (
      <div className="card" aria-busy="true">
        <div className="skeleton" style={{ height: "1.25rem", width: "12rem", marginBottom: "0.75rem" }} />
        <div className="skeleton" style={{ height: "4rem" }} />
        <div className="skeleton" style={{ height: "2.5rem", marginTop: "0.75rem" }} />
      </div>
    );
  }
  
  if (configError) {
    return (
      <div className="alert alert-error" role="alert">
        Failed to load chat configuration. Check that the API server is reachable.
      </div>
    );
  }

  return (
    <DisplayModeProvider>
      <div className="chat-page">
      <div className="chat-main">
        <ChatToolbar 
           modelName={activeModel} 
           onOpenSettings={() => setDrawerOpen(!drawerOpen)} 
        />
        
        <ErrorBoundary>
          <ChatThread 
             turns={turns} 
             busy={busy} 
             onPrompt={(prompt) => {
                setInput(prompt);
                setTimeout(() => send(prompt), 50); // Small delay to let input update
             }}
          />
        </ErrorBoundary>

        <ChatComposer 
           input={input} 
           setInput={setInput} 
           onSend={() => {
              if (input.trim()) {
                 const text = input;
                 setInput("");
                 send(text);
              }
           }} 
           onStop={stop} 
           busy={busy} 
           turns={turns}
        />
      </div>

      <SettingsDrawer 
         open={drawerOpen} 
         onClose={() => setDrawerOpen(false)} 
         model={model} 
         setModel={setModel} 
         config={config} 
      />
    </div>
    </DisplayModeProvider>
  );
}
