import { memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { Icon } from "../../components/Icon";
import type { LocalChatMessage } from "./useChat";

import { AssistantStatus } from "./AssistantStatus";

export const MessageRenderer = memo(({ turn, isLast }: { turn: LocalChatMessage; isLast: boolean }) => {
  if (turn.role === "user") {
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

  if (turn.role === "assistant" || turn.role === "system") {
    return (
      <div className="chat-message-wrapper assistant slide-up">
        <div className="chat-message">
          <div className="chat-avatar assistant">
            <Icon name="moon" style={{ width: "1.1rem", height: "1.1rem" }} />
          </div>
          <div className="chat-message-content markdown-body">
            {turn.content && (
              <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
                {turn.content}
              </ReactMarkdown>
            )}
            {isLast && turn.state === "streaming" && (
               <div style={{ marginTop: "0.5rem" }}><AssistantStatus state="streaming" /></div>
            )}
            {turn.state === "error" && (
               <div className="alert alert-error" style={{marginTop: "0.5rem"}}>
                 An error occurred generating the response.
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

  if (turn.role === "artifact") {
    return (
      <div className="chat-message-wrapper assistant">
        <div className="chat-message">
          <div className="chat-avatar" style={{background: "transparent"}} />
          <div className="chat-message-content">
            {turn.artifact_type.startsWith("image") ? (
              <div className="border border-gray-200 p-2 rounded-lg bg-gray-50 max-w-sm">
                <img src={turn.url} alt="Screenshot" className="max-w-full rounded" />
                <div className="text-xs text-gray-500 mt-2 truncate">Screenshot captured</div>
              </div>
            ) : (
              <a href={turn.url} target="_blank" rel="noreferrer" className="flex items-center gap-2 border border-gray-200 p-3 rounded-lg bg-white shadow-sm hover:bg-gray-50 transition w-max">
                <Icon name="downloads" className="w-5 h-5 text-blue-500" />
                <span className="font-medium text-gray-700">Download File</span>
              </a>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (turn.role === "error") {
    return (
      <div className="chat-message-wrapper assistant">
        <div className="chat-message">
          <div className="chat-avatar" style={{background: "transparent"}} />
          <div className="chat-message-content">
            <div className="alert alert-error">Error: {turn.error.message}</div>
          </div>
        </div>
      </div>
    );
  }

  return null;
});
