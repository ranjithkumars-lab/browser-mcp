import { useCallback, useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getChatConfig, chatStream, type ChatMessage } from "../services/chat";

type Turn =
  | { kind: "user"; content: string }
  | { kind: "assistant"; content: string; streaming?: boolean }
  | { kind: "tool_call"; name: string; arguments: Record<string, unknown> }
  | { kind: "tool_result"; name: string; content: string; error: boolean };

function jsonText(value: Record<string, unknown>): string {
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function truncate(value: string, max = 600): string {
  return value.length > max ? `${value.slice(0, max)}\u2026` : value;
}

export function Chat() {
  const { data: config, isLoading: loadingConfig, error: configError } = useQuery({
    queryKey: ["chat-config"],
    queryFn: getChatConfig,
  });

  const [model, setModel] = useState<string | undefined>(undefined);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const activeModel = model ?? config?.model ?? "";

  const scrollToBottom = useCallback(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(scrollToBottom, [turns, scrollToBottom]);

  useEffect(() => () => abortRef.current?.abort(), []);

  const send = useCallback(async () => {
    const content = input.trim();
    if (!content || busy) return;

    const messages: ChatMessage[] = turns
      .filter((t) => t.kind === "user" || t.kind === "assistant")
      .map((t) =>
        t.kind === "user"
          ? { role: "user" as const, content: t.content }
          : { role: "assistant" as const, content: t.content },
      );
    messages.push({ role: "user", content });

    setInput("");
    setError(null);
    setTurns((prev) => [...prev, { kind: "user", content }]);
    setBusy(true);

    const controller = new AbortController();
    abortRef.current = controller;
    let assistantContent = "";

    try {
      for await (const event of chatStream(messages, model || undefined, controller.signal)) {
        if (event.type === "text") {
          assistantContent += event.delta;
          setTurns((prev) => {
            const last = prev[prev.length - 1];
            if (last?.kind === "assistant" && last.streaming) {
              return [...prev.slice(0, -1), { kind: "assistant", content: assistantContent, streaming: true }];
            }
            return [...prev, { kind: "assistant", content: assistantContent, streaming: true }];
          });
        } else if (event.type === "tool_call") {
          setTurns((prev) => [
            ...prev,
            { kind: "tool_call", name: event.name, arguments: event.arguments },
          ]);
        } else if (event.type === "tool_result") {
          setTurns((prev) => [
            ...prev,
            { kind: "tool_result", name: event.name, content: event.content, error: event.error },
          ]);
        } else if (event.type === "error") {
          setError(event.detail);
        }
      }
      setTurns((prev) => {
        const streaming = prev[prev.length - 1]?.kind === "assistant";
        const next = streaming ? prev.slice(0, -1) : prev;
        return [...next, { kind: "assistant", content: assistantContent }];
      });
    } catch (err) {
      const message = err instanceof DOMException && err.name === "AbortError"
        ? "Stopped."
        : err instanceof Error
          ? err.message
          : String(err);
      setError(message);
    } finally {
      setBusy(false);
      abortRef.current = null;
    }
  }, [busy, input, model, turns]);

  if (loadingConfig) return <div className="card">Loading chat...</div>;
  if (configError) return <div className="card">Failed to load chat configuration</div>;

  return (
    <div className="card chat-card">
      <div className="chat-head">
        <h3>Ollama Chat</h3>
        <label className="chat-model">
          Model
          <input
            list="ollama-models"
            value={activeModel}
            placeholder="model"
            aria-label="Ollama model"
            onChange={(e) => setModel(e.target.value)}
          />
          <datalist id="ollama-models">
            {config ? <option value={config.model} /> : null}
          </datalist>
        </label>
      </div>
      <p className="muted">
        {config ? `${config.tools} browser tools available via ${config.host}` : ""}
      </p>

      {turns.length === 0 ? (
        <div className="empty">
          <p>Ask the agent to browse, scrape, or automate the web.</p>
        </div>
      ) : (
        <div className="chat-thread" aria-live="polite">
          {turns.map((turn, index) => {
            if (turn.kind === "user") {
              return (
                <div key={index} className="chat-msg chat-user">
                  <div>{turn.content}</div>
                </div>
              );
            }
            if (turn.kind === "assistant") {
              return (
                <div key={index} className="chat-msg chat-agent">
                  <pre className="chat-pre">{turn.content || (turn.streaming ? "\u2026" : "")}</pre>
                </div>
              );
            }
            if (turn.kind === "tool_call") {
              return (
                <div key={index} className="chat-tool">
                  <strong>{turn.name}</strong>
                  <code>{jsonText(turn.arguments)}</code>
                </div>
              );
            }
            return (
              <div key={index} className="chat-tool" role={turn.error ? "alert" : undefined}>
                <strong>{turn.name}</strong>
                <pre>{truncate(turn.content)}</pre>
              </div>
            );
          })}
          <div ref={scrollRef} />
        </div>
      )}

      {busy && <div className="muted">Agent is working\u2026</div>}
      {error && <div className="chat-error" role="alert">{error}</div>}

      <form
        className="chat-compose"
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <textarea
          rows={3}
          value={input}
          placeholder="Describe a browser task\u2026"
          aria-label="Message"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void send();
            }
          }}
        />
        <div className="chat-actions">
          {busy ? (
            <button
              type="button"
              className="danger"
              onClick={() => abortRef.current?.abort()}
            >
              Stop
            </button>
          ) : (
            <button type="submit" disabled={!input.trim()}>
              Send
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
