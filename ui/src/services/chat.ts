import { UiError, request } from "./client";

export interface ChatMessage {
  role: "system" | "user" | "assistant" | "tool";
  content: string;
  name?: string;
}

export type ChatEvent =
  | { type: "text"; delta: string }
  | { type: "tool_call"; name: string; arguments: Record<string, unknown> }
  | { type: "tool_result"; name: string; content: string; error: boolean }
  | { type: "done"; content: string; steps: number }
  | { type: "error"; detail: string };

export interface ChatConfig {
  host: string;
  model: string;
  tools: number;
}

export const getChatConfig = () => request<ChatConfig>("/api/v1/chat/config");

function parseSseBlock(block: string): ChatEvent | null {
  const eventLine = block.match(/^event: (.+)$/m)?.[1];
  const dataLine = block.match(/^data: (.+)$/ms)?.[1];
  if (!eventLine || dataLine === undefined) return null;
  try {
    const payload = JSON.parse(dataLine) as Record<string, unknown>;
    return { type: eventLine, ...payload } as ChatEvent;
  } catch {
    return null;
  }
}

export async function* chatStream(
  messages: ChatMessage[],
  model?: string,
  signal?: AbortSignal,
): AsyncGenerator<ChatEvent> {
  const response = await fetch("/api/v1/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, model }),
    signal,
  });
  if (!response.ok || !response.body) {
    throw new UiError(response.status, await response.text().catch(() => response.statusText));
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";
    for (const block of blocks) {
      const event = parseSseBlock(block);
      if (event) yield event;
    }
  }
  if (buffer.trim()) {
    const event = parseSseBlock(buffer);
    if (event) yield event;
  }
}
