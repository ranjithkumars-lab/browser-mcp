export type TurnState = "queued" | "loading" | "streaming" | "completed" | "error" | "cancelled";

export interface BaseMessage {
  role: string;
  id?: string;
  timestamp?: string;
}

export interface UserMessage extends BaseMessage {
  role: "user";
  content: string;
}

export interface AssistantMessage extends BaseMessage {
  role: "assistant";
  content: string;
}

export interface ToolMessage extends BaseMessage {
  role: "tool";
  name: string;
  content: string;
  tool_call_id?: string;
}

export interface ArtifactMessage extends BaseMessage {
  role: "artifact";
  artifact_id: string;
  artifact_type: string;
  url: string;
  metadata: Record<string, any>;
}

export interface SystemMessage extends BaseMessage {
  role: "system";
  content: string;
}

export interface ProgressMessage extends BaseMessage {
  role: "progress";
  step: string;
  status: "pending" | "running" | "success" | "failed";
  details?: string;
}

export interface PlanningMessage extends BaseMessage {
  role: "planning";
  plan: string[];
}

export interface StatusMessage extends BaseMessage {
  role: "status";
  content: string;
}

export interface TypedError {
  type: "ToolError" | "BrowserError" | "TimeoutError" | "ValidationError" | "AuthenticationError" | "RetryableError";
  message: string;
  details?: Record<string, any>;
}

export interface ErrorMessage extends BaseMessage {
  role: "error";
  error: TypedError;
}

export type ChatMessage =
  | UserMessage
  | AssistantMessage
  | ToolMessage
  | ArtifactMessage
  | SystemMessage
  | ProgressMessage
  | PlanningMessage
  | StatusMessage
  | ErrorMessage;

export type Turn = ChatMessage; // Keep Turn alias for backward compatibility for now if needed, but preferably use ChatMessage.
