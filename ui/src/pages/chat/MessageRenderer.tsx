import React, { memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { Icon } from "../../components/Icon";
import type { LocalChatMessage } from "./useChat";
import { useDisplayMode } from "./DisplayModeContext";
import { AssistantStatus } from "./AssistantStatus";
import type { WorkflowMessage, SummaryMessage, ArtifactMessage, ErrorMessage, UserMessage, AssistantMessage } from "./types";

// 1. Individual Renderers

const UserRenderer = ({ message }: { message: UserMessage }) => (
  <div className="chat-message-wrapper user slide-up">
    <div className="chat-message" style={{ flexDirection: "row-reverse" }}>
      <div className="chat-avatar user">
        <Icon name="user" style={{ width: "1rem", height: "1rem" }} />
      </div>
      <div className="chat-message-content" style={{ display: "flex", justifyContent: "flex-end" }}>
         <div style={{ background: "var(--bg-elevated)", padding: "0.5rem 1rem", borderRadius: "1.25rem", borderTopRightRadius: "0.25rem", display: "inline-block" }}>
           {message.content}
         </div>
      </div>
    </div>
  </div>
);

const AssistantRenderer = ({ message, isLast }: { message: AssistantMessage & { state?: string }, isLast: boolean }) => (
  <div className="chat-message-wrapper assistant slide-up">
    <div className="chat-message">
      <div className="chat-avatar assistant">
        <Icon name="moon" style={{ width: "1.1rem", height: "1.1rem" }} />
      </div>
      <div className="chat-message-content markdown-body">
        {message.content && (
          <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
            {message.content}
          </ReactMarkdown>
        )}
        {isLast && message.state === "streaming" && (
           <div style={{ marginTop: "0.5rem" }}><AssistantStatus state="streaming" /></div>
        )}
        {message.state === "error" && (
           <div className="alert alert-error" style={{marginTop: "0.5rem"}}>
             An error occurred generating the response.
           </div>
        )}
        {message.state === "cancelled" && (
           <div style={{ fontSize: "var(--text-sm)", color: "var(--muted)", marginTop: "0.5rem" }}>
             Stopped generating.
           </div>
        )}
      </div>
    </div>
  </div>
);

const SummaryRenderer = ({ message }: { message: SummaryMessage }) => (
  <div className="chat-message-wrapper assistant slide-up">
    <div className="chat-message">
      <div className="chat-avatar assistant" style={{ background: "var(--accent-strong)" }}>
        <Icon name="chat" style={{ width: "1.1rem", height: "1.1rem" }} />
      </div>
      <div className="chat-message-content markdown-body">
        <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
          {message.content}
        </ReactMarkdown>
      </div>
    </div>
  </div>
);

const ArtifactCard = ({ message }: { message: ArtifactMessage }) => (
  <div className="chat-message-wrapper assistant">
    <div className="chat-message">
      <div className="chat-avatar" style={{background: "transparent"}} />
      <div className="chat-message-content">
        {message.artifact_type.startsWith("image") ? (
          <div style={{ border: "1px solid var(--border)", padding: "0.5rem", borderRadius: "var(--radius-lg)", background: "var(--surface-2)", maxWidth: "24rem" }}>
            <img src={message.url} alt="Artifact preview" style={{ maxWidth: "100%", borderRadius: "var(--radius-md)" }} />
            <div style={{ fontSize: "var(--text-xs)", color: "var(--text-secondary)", marginTop: "0.5rem", textOverflow: "ellipsis", overflow: "hidden" }}>Screenshot captured</div>
          </div>
        ) : (
          <a href={message.url} target="_blank" rel="noreferrer" style={{ display: "flex", alignItems: "center", gap: "0.5rem", border: "1px solid var(--border)", padding: "0.75rem", borderRadius: "var(--radius-lg)", background: "var(--surface)", textDecoration: "none", width: "max-content" }}>
            <Icon name="downloads" style={{ width: "1.25rem", height: "1.25rem", color: "var(--accent)" }} />
            <span style={{ fontWeight: 500, color: "var(--text)" }}>Download File</span>
          </a>
        )}
      </div>
    </div>
  </div>
);

const WorkflowCard = ({ message }: { message: WorkflowMessage }) => (
  <div className="chat-message-wrapper assistant">
    <div className="chat-message">
      <div className="chat-avatar" style={{background: "transparent"}} />
      <div className="chat-message-content">
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", padding: "0.75rem", background: "var(--surface-2)", borderRadius: "var(--radius-lg)", border: "1px solid var(--border)" }}>
          <Icon name="jobs" style={{ width: "1.2rem", height: "1.2rem", color: message.status === "success" ? "var(--success)" : message.status === "failed" ? "red" : "var(--text-secondary)" }} />
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span style={{ fontWeight: 600, fontSize: "var(--text-sm)" }}>{message.workflow_type.toUpperCase()}</span>
            <span style={{ fontSize: "var(--text-xs)", color: "var(--text-secondary)" }}>Status: {message.status}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
);

const ErrorCard = ({ message }: { message: ErrorMessage }) => (
  <div className="chat-message-wrapper assistant">
    <div className="chat-message">
      <div className="chat-avatar" style={{background: "transparent"}} />
      <div className="chat-message-content">
        <div className="alert alert-error" style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          <strong>Error: {message.error.type}</strong>
          <span>{message.error.message}</span>
          <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem" }}>
            <button className="btn btn-primary" style={{ padding: "0.25rem 0.5rem", fontSize: "var(--text-xs)" }}>Retry</button>
            <button className="btn" style={{ padding: "0.25rem 0.5rem", fontSize: "var(--text-xs)" }}>Abort</button>
          </div>
        </div>
      </div>
    </div>
  </div>
);

// 2. Renderer Registry
const Registry: Record<string, React.FC<any>> = {
  user: UserRenderer,
  assistant: AssistantRenderer,
  summary: SummaryRenderer,
  artifact: ArtifactCard,
  workflow: WorkflowCard,
  error: ErrorCard,
};

// 3. Presentation Layer
export const MessageRenderer = memo(({ turn, isLast }: { turn: LocalChatMessage; isLast: boolean }) => {
  const { mode } = useDisplayMode();

  // Visibility logic based on mode
  if (mode === "simple") {
    // In simple mode, only show user prompts, final answers/summaries, and artifacts/errors. Hide raw tool calls, workflow steps.
    if (!["user", "assistant", "summary", "artifact", "error"].includes(turn.role)) {
      return null;
    }
  }

  if (mode === "advanced") {
    // In advanced, show workflows too, but maybe hide raw JSON/tool calls if they existed as a specific role
    if (!["user", "assistant", "summary", "artifact", "error", "workflow"].includes(turn.role)) {
      return null;
    }
  }

  // mode === "developer" shows everything (including raw tool logs if we pass them)

  // System role fallback
  const roleToRender = turn.role === "system" ? "assistant" : turn.role;
  const Renderer = Registry[roleToRender];

  if (!Renderer) {
    // If we have no renderer for this type but we are in developer mode, dump it as raw JSON
    if (mode === "developer") {
      return (
         <div className="chat-message-wrapper assistant">
            <div className="chat-message">
               <div className="chat-avatar" style={{background: "transparent"}} />
               <div className="chat-message-content">
                  <pre style={{ fontSize: "var(--text-xs)", background: "var(--surface-2)", padding: "0.5rem", borderRadius: "var(--radius-sm)" }}>
                     {JSON.stringify(turn, null, 2)}
                  </pre>
               </div>
            </div>
         </div>
      );
    }
    return null;
  }

  return <Renderer message={turn} isLast={isLast} />;
});
