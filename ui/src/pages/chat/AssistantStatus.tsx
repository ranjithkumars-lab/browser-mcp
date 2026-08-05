import { memo } from "react";
import { Icon } from "../../components/Icon";
import type { TurnState } from "./types";

export const AssistantStatus = memo(({ state, toolName }: { state: TurnState; toolName?: string }) => {
  if (state === "queued") return null;
  
  if (toolName && state === "completed") {
    return (
      <div className="assistant-status fade-in">
        <Icon name="check" style={{width: "1rem", height: "1rem", color: "var(--success)"}}/>
        <span>Ran {toolName}</span>
      </div>
    );
  }

  if (state === "loading" || state === "streaming" || (toolName && state !== "completed")) {
    return (
      <div className="assistant-status fade-in" aria-live="polite">
        <div className="typing-indicator"><span /><span /><span /></div>
        <span>{toolName ? `Running ${toolName}...` : "Thinking..."}</span>
      </div>
    );
  }

  return null;
});
