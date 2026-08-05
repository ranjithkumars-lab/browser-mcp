import { useCallback, useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getChatConfig, chatStream, type ChatMessage } from "../services/chat";
import { Icon } from "../components/Icon";
import { Markdown } from "../utils/markdown";

type Turn =
  | { kind: "user"; content: string }
  | { kind: "assistant"; content: string; streaming?: boolean }
  | { kind: "tool_call"; name: string }
  | { kind: "tool_result"; name: string; content: string; error: boolean };

const USER_ID_KEY = "browser-mcp-user-id";

function currentUserId(): string {
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

type ScreenshotMeta = {
  url: string | null;
  caption: string | null;
};

function screenshotMeta(content: string): ScreenshotMeta {
  try {
    const data = JSON.parse(content) as Record<string, unknown>;
    const artifactId = typeof data?.artifact_id === "string" ? data.artifact_id : null;
    if (artifactId) {
      return {
        url: `/api/v1/artifacts/${encodeURIComponent(artifactId)}`,
        caption: typeof data?.filename === "string" ? data.filename : "Screenshot",
      };
    }
    const path = typeof data?.screenshot_path === "string" ? data.screenshot_path : "";
    const filename = path ? String(path.split(/[\\/]/).pop()) : "";
    const url = filename ? `/api/v1/screenshots/${encodeURIComponent(filename)}` : null;
    const title = typeof data?.title === "string" && data.title ? data.title : null;
    const pageUrl = typeof data?.url === "string" && data.url ? data.url : null;
    return {
      url,
      caption: title ?? pageUrl ?? `Screenshot${data?.format ? ` (${data.format})` : ""}`,
    };
  } catch {
    return { url: null, caption: null };
  }
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
  const userId = currentUserId();

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
      for await (const event of chatStream(messages, model || undefined, userId, controller.signal)) {
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
            { kind: "tool_call", name: event.name },
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
      <div className="chat-main">
        {turns.length === 0 && !busy ? (
          <div className="state" style={{ margin: "var(--space-5)", marginTop: "var(--space-7)", alignSelf: "center" }}>
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
                  </div>
                );
              }
              return (
                <div key={index} className={`tool-row${turn.error ? " error" : ""}`} role={turn.error ? "alert" : undefined}>
                  <div className="tool-name">
                    {turn.name} <code>{turn.error ? "error" : "result"}</code>
                  </div>
                  {!turn.error && turn.name === "browser.screenshot" && (() => {
                    const meta = screenshotMeta(turn.content);
                    return meta.url ? (
                      <figure className="tool-screenshot">
                        <a
                          href={meta.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          title="Open full-size screenshot in a new tab"
                        >
                          <img loading="lazy" src={meta.url} alt={meta.caption ?? "Screenshot"} />
                        </a>
                      </figure>
                    ) : null;
                  })()}
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

        <div className="chat-compose-wrapper">
          <form
            className="chat-compose"
            onSubmit={(e) => {
              e.preventDefault();
              void send();
            }}
          >
            <textarea
              rows={1}
              value={input}
              placeholder="Message Browser MCP..."
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
              <span className="chat-hint">Enter to send &middot; Shift+Enter for a new line</span>
              {busy ? (
                <button type="button" className="btn btn-danger" onClick={() => abortRef.current?.abort()}>
                  Stop
                </button>
              ) : (
                <button type="submit" className="btn btn-primary" disabled={!input.trim()}>
                  <Icon name="play" />
                </button>
              )}
            </div>
            {error && <div className="alert alert-error" role="alert" style={{marginTop: "0.5rem"}}>{error}</div>}
          </form>
        </div>
      </div>

      <div className="settings-drawer">
        <div className="card">
          <div className="card-title">Agent Settings</div>
          <div className="card-sub">Configure Ollama Model</div>
          <div style={{ marginTop: "var(--space-4)", display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
            <label className="field">
              <span>Model</span>
              <input
                className="input"
                list="ollama-models"
                value={activeModel}
                placeholder="Model"
                aria-label="Ollama model"
                onChange={(e) => setModel(e.target.value)}
              />
            </label>
            <datalist id="ollama-models">
              {config ? <option value={config.model} /> : null}
            </datalist>
            <div>
              <span className="badge badge-muted">{config?.host ?? ""}</span>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="card-title">Available tools</div>
          <div className="card-sub">{config?.tools ?? 0} active tools</div>
          <div className="tools-panel" style={{marginTop: "0.5rem"}}>
            {(config?.tool_names ?? []).map((name) => (
              <div className="tool-item" style={{padding: "0.25rem 0"}} key={name}>
                <code>{name}</code>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
