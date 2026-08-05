import { useCallback, useEffect, useRef, useState } from "react";
import { chatStream, type ChatMessage } from "../../services/chat";

const USER_ID_KEY = "browser-mcp-user-id";

export function currentUserId(): string {
  try {
    const existing = localStorage.getItem(USER_ID_KEY);
    if (existing) return existing;
    const id = crypto.randomUUID();
    localStorage.setItem(USER_ID_KEY, id);
    return id;
  } catch {
    return "anonymous";
  }
}

export type LocalChatMessage = ChatMessage & { state?: string };

export function useChat(model: string | undefined) {
  const [turns, setTurns] = useState<LocalChatMessage[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const abortRef = useRef<AbortController | null>(null);
  const userId = currentUserId();

  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setBusy(false);
    setTurns((prev) => {
      const last = prev[prev.length - 1];
      if (last && last.role === "assistant" && last.state === "streaming") {
        return [...prev.slice(0, -1), { ...last, state: "cancelled" } as LocalChatMessage];
      }
      return prev;
    });
  }, []);

  const send = useCallback(async (content: string) => {
    content = content.trim();
    if (!content || busy) return;

    const messages = turns.map(t => {
      // Omit local UI state before sending
      const { state, ...rest } = t;
      return rest as ChatMessage;
    });
    
    // Actually, only user and assistant messages need to be sent back normally
    const history = messages.filter(m => m.role === "user" || m.role === "assistant");
    
    history.push({ role: "user", content });

    setError(null);
    setTurns((prev) => [...prev, { role: "user", content }]);
    setBusy(true);

    const controller = new AbortController();
    abortRef.current = controller;
    let assistantContent = "";

    try {
      for await (const event of chatStream(history, model || undefined, userId, controller.signal)) {
        if (event.type === "text") {
          assistantContent += event.delta;
          setTurns((prev) => {
            const last = prev[prev.length - 1];
            if (last?.role === "assistant" && (last.state === "streaming" || last.state === "loading" || last.state === "queued")) {
              return [...prev.slice(0, -1), { role: "assistant", content: assistantContent, state: "streaming" }];
            }
            return [...prev, { role: "assistant", content: assistantContent, state: "streaming" }];
          });
        } else if (event.type === "tool_call") {
          setTurns((prev) => [
            ...prev,
            { role: "tool", name: event.name, content: "Tool called", state: "completed" },
          ]);
        } else if (event.type === "message") {
          // This captures our new ArtifactMessage, StatusMessage, etc.
          const { type, ...msgProps } = event;
          setTurns((prev) => [...prev, msgProps as LocalChatMessage]);
        } else if (event.type === "error") {
          setError(event.detail);
          setTurns((prev) => {
             const last = prev[prev.length - 1];
             if (last?.role === "assistant" && last.state === "streaming") {
                return [...prev.slice(0, -1), { role: "assistant", content: assistantContent, state: "error" }];
             }
             return prev;
          });
        } else if (event.type === "done") {
          setTurns((prev) => {
            const last = prev[prev.length - 1];
            if (last?.role === "assistant" && last.state === "streaming") {
              const finalContent = event.content ?? last.content;
              return [...prev.slice(0, -1), { role: "assistant", content: finalContent, state: "completed" }];
            }
            return prev;
          });
        }
      }
    } catch (err) {
      const message = err instanceof DOMException && err.name === "AbortError"
        ? "Stopped."
        : err instanceof Error
          ? err.message
          : String(err);
      
      if (err instanceof DOMException && err.name === "AbortError") {
         // handled by stop()
      } else {
         setError(message);
         setTurns((prev) => {
            const last = prev[prev.length - 1];
            if (last?.role === "assistant" && last.state === "streaming") {
               return [...prev.slice(0, -1), { role: "assistant", content: assistantContent, state: "error" }];
            }
            return prev;
         });
      }
    } finally {
      setBusy(false);
      abortRef.current = null;
    }
  }, [busy, model, turns, userId]);

  return { turns, busy, error, send, stop };
}
