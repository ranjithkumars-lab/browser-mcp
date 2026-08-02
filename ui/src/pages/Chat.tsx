import { useCallback, useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getChatConfig, chatStream, type ChatMessage } from "../services/chat";
import { Icon } from "../components/Icon";
import { Markdown } from "../utils/markdown";

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

  useEffect(scrollToBottom, [turns, busy, scrollToBottom]);

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
        } else if (event.type === "done") {
          setTurns((prev) => {
            const last = prev[prev.length - 1];
            if (last?.kind === "assistant" && last.streaming) {
              return [...prev.slice(0, -1), { kind: "assistant", content: last.content, streaming: false }];
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
      setError(message);
    } finally {
      setBusy(false);
      abortRef.current = null;
    }
  }, [busy, input, model, turns]);

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

  const lastTurn = turns[turns.length - 1];
  const streamingAssistant = lastTurn?.kind === "assistant" && lastTurn.streaming === true;

  return (
    <div className="chat-layout">
      <div className="card chat-card">
        <div className="chat-head">
          <div>
            <div className="card-title">Ollama Chat</div>
            <div className="card-sub">{config ? `${config.tools} browser tools available via ${config.host}` : ""}</div>
          </div>
          <label className="chat-model">
            Model
            <input
              className="input"
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

        {turns.length === 0 && !busy ? (
          <div className="state" style={{ margin: "var(--space-5)", marginTop: "var(--space-7)" }}>
            <div className="state-icon"><Icon name="chat" style={{ width: "2.5rem", height: "2.5rem" }} /></div>
            <div className="state-title">Ask the agent to browse the web</div>
            <div className="state-sub">
              The agent can navigate pages, take snapshots, search the web, extract data, and run browser automations.
            </div>
          </div>
        ) : (
          <div className="chat-thread" aria-live="polite">
            {turns.map((turn, index) => {
              if (turn.kind === "user") {
                return (
                  <div key={index} className="chat-msg chat-user">
                    <div className="chat-bubble">{turn.content}</div>
                  </div>
                );
              }
              if (turn.kind === "assistant") {
                return (
                  <div key={index} className="chat-msg chat-agent">
                    <div className="chat-role">Assistant</div>
                    <div className="chat-bubble">
                      {turn.streaming && !turn.content ? (
                        <div className="typing"><span /><span /><span /></div>
                      ) : (
                        <Markdown text={turn.content} />
                      )}
                    </div>
                  </div>
                );
              }
              if (turn.kind === "tool_call") {
                return (
                  <div key={index} className="tool-row">
                    <div className="tool-name">
                      {turn.name} <code>tool call</code>
                    </div>
                    <pre className="tool-args">{jsonText(turn.arguments)}</pre>
                  </div>
                );
              }
              return (
                <div key={index} className={`tool-row${turn.error ? " error" : ""}`} role={turn.error ? "alert" : undefined}>
                  <div className="tool-name">
                    {turn.name} <code>{turn.error ? "error" : "result"}</code>
                  </div>
                  <pre className="tool-out">{truncate(turn.content)}</pre>
                </div>
              );
            })}

            {busy && !streamingAssistant && (
              <div className="chat-msg chat-agent">
                <div className="chat-role">Assistant</div>
                <div className="chat-bubble"><div className="typing"><span /><span /><span /></div></div>
              </div>
            )}
            <div ref={scrollRef} />
          </div>
        )}

        {error && <div className="alert alert-error" role="alert">{error}</div>}

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
              <button type="button" className="btn btn-danger" onClick={() => abortRef.current?.abort()}>
                Stop
              </button>
            ) : (
              <button type="submit" className="btn btn-primary" disabled={!input.trim()}>
                Send
              </button>
            )}
            <span className="chat-hint">Enter to send &middot; Shift+Enter for a new line</span>
          </div>
        </form>
      </div>

      <div className="chat-side">
        <div className="card">
          <div className="card-title">Ollama</div>
          <div className="card-sub">Server model for the agent loop</div>
          <div style={{ marginTop: "var(--space-4)", display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
            <div>
              <span className="badge badge-accent">{config?.model ?? "gpt-oss:20b"}</span>
            </div>
            <div>
              <span className="badge badge-muted">{config?.host ?? ""}</span>
            </div>
            <div>
              <span className="badge badge-info">{config?.tools ?? 0} tools</span>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="card-title">Available tools</div>
          <div className="card-sub">Injected into every agent run</div>
          <div className="tools-panel">
            {(config?.tool_names ?? []).map((name) => (
              <div className="tool-item" key={name}>
                <code>{name}</code>
                <span className="badge badge-muted">tool</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
