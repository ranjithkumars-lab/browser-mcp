import { useCallback, useEffect, useRef, useState } from "react";
import { chatStream, type ChatMessage } from "../../services/chat";
import type { Turn } from "./types";

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

export function useChat(model: string | undefined) {
  const [turns, setTurns] = useState<Turn[]>([]);
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
      if (last && (last.kind === "assistant" || last.kind === "tool_call") && last.state === "streaming") {
        return [...prev.slice(0, -1), { ...last, state: "cancelled" } as Turn];
      }
      return prev;
    });
  }, []);

  const send = useCallback(async (content: string) => {
    content = content.trim();
    if (!content || busy) return;

    const messages: ChatMessage[] = turns
      .filter((t) => t.kind === "user" || t.kind === "assistant")
      .map((t) =>
        t.kind === "user"
          ? { role: "user" as const, content: t.content }
          : { role: "assistant" as const, content: t.content },
      );
    messages.push({ role: "user", content });

    setError(null);
    setTurns((prev) => [...prev, { kind: "user", content }]);
    setBusy(true);

    const controller = new AbortController();
    abortRef.current = controller;
    let assistantContent = "";

    try {
      for await (const event of chatStream(messages, model || undefined, userId, controller.signal)) {
        if (event.type === "text") {
          assistantContent += event.delta;
          setTurns((prev) => {
            const last = prev[prev.length - 1];
            if (last?.kind === "assistant" && (last.state === "streaming" || last.state === "loading" || last.state === "queued")) {
              return [...prev.slice(0, -1), { kind: "assistant", content: assistantContent, state: "streaming" }];
            }
            return [...prev, { kind: "assistant", content: assistantContent, state: "streaming" }];
          });
        } else if (event.type === "tool_call") {
          setTurns((prev) => [
            ...prev,
            { kind: "tool_call", name: event.name, state: "completed" },
          ]);
        } else if (event.type === "tool_result") {
          setTurns((prev) => [
            ...prev,
            { kind: "tool_result", name: event.name, content: event.content, error: event.error },
          ]);
        } else if (event.type === "error") {
          setError(event.detail);
          setTurns((prev) => {
             const last = prev[prev.length - 1];
             if (last?.kind === "assistant" && last.state === "streaming") {
                return [...prev.slice(0, -1), { kind: "assistant", content: assistantContent, state: "error", errorDetail: event.detail }];
             }
             return prev;
          });
        } else if (event.type === "done") {
          setTurns((prev) => {
            const last = prev[prev.length - 1];
            if (last?.kind === "assistant" && last.state === "streaming") {
              return [...prev.slice(0, -1), { kind: "assistant", content: last.content, state: "completed" }];
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
            if (last?.kind === "assistant" && last.state === "streaming") {
               return [...prev.slice(0, -1), { kind: "assistant", content: assistantContent, state: "error", errorDetail: message }];
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
