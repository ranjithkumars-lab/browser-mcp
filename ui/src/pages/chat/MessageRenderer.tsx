import { memo } from "react";
import { Markdown } from "../../utils/markdown";
import { Icon } from "../../components/Icon";
import type { Turn } from "./types";
import { ArtifactRenderer } from "./ArtifactRenderer";
import { AssistantStatus } from "./AssistantStatus";

export const MessageRenderer = memo(({ turn, isLast }: { turn: Turn; isLast: boolean }) => {
  if (turn.kind === "user") {
    return (
      <div className="chat-message-wrapper user slide-up">
        <div className="chat-message" style={{ flexDirection: "row-reverse" }}>
          <div className="chat-avatar user">
            <Icon name="user" style={{ width: "1rem", height: "1rem" }} />
          </div>
          <div className="chat-message-content" style={{ display: "flex", justifyContent: "flex-end" }}>
             <div style={{ background: "var(--bg-elevated)", padding: "0.5rem 1rem", borderRadius: "1.25rem", borderTopRightRadius: "0.25rem", display: "inline-block" }}>
               {turn.content}
             </div>
          </div>
        </div>
      </div>
    );
  }

  if (turn.kind === "assistant") {
    return (
      <div className="chat-message-wrapper assistant slide-up">
        <div className="chat-message">
          <div className="chat-avatar assistant">
            <Icon name="moon" style={{ width: "1.1rem", height: "1.1rem" }} />
          </div>
          <div className="chat-message-content">
            {turn.content && <Markdown text={turn.content} />}
            {isLast && turn.state === "streaming" && (
               <div style={{ marginTop: "0.5rem" }}><AssistantStatus state="streaming" /></div>
            )}
            {turn.state === "error" && (
               <div className="alert alert-error" style={{marginTop: "0.5rem"}}>
                 {turn.errorDetail || "An error occurred generating the response."}
               </div>
            )}
            {turn.state === "cancelled" && (
               <div style={{ fontSize: "var(--text-sm)", color: "var(--muted)", marginTop: "0.5rem" }}>
                 Stopped generating.
               </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (turn.kind === "tool_call") {
    return (
      <div className="chat-message-wrapper assistant">
        <div className="chat-message">
          <div className="chat-avatar" style={{background: "transparent"}} />
          <div className="chat-message-content">
            <AssistantStatus state={turn.state} toolName={turn.name} />
          </div>
        </div>
      </div>
    );
  }

  if (turn.kind === "tool_result") {
    if (!turn.error && turn.name === "browser.screenshot") {
      return (
        <div className="chat-message-wrapper assistant">
          <div className="chat-message">
            <div className="chat-avatar" style={{background: "transparent"}} />
            <div className="chat-message-content">
              <ArtifactRenderer content={turn.content} />
            </div>
          </div>
        </div>
      );
    }
    if (turn.error) {
      return (
        <div className="chat-message-wrapper assistant">
          <div className="chat-message">
            <div className="chat-avatar" style={{background: "transparent"}} />
            <div className="chat-message-content">
              <div className="alert alert-error">Tool error: {turn.name}</div>
            </div>
          </div>
        </div>
      );
    }
  }

  return null;
});
