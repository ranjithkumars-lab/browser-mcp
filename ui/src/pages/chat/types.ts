export type TurnState = "queued" | "loading" | "streaming" | "completed" | "error" | "cancelled";

export type Turn =
  | { kind: "user"; content: string }
  | { kind: "assistant"; content: string; state: TurnState; errorDetail?: string }
  | { kind: "tool_call"; name: string; state: TurnState }
  | { kind: "tool_result"; name: string; content: string; error: boolean };

export type ScreenshotMeta = {
  url: string | null;
  caption: string | null;
};
