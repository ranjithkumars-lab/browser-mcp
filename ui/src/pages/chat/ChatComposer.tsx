import { memo, KeyboardEvent, useRef, useEffect, useState } from "react";
import { Icon } from "../../components/Icon";
import { LocalChatMessage } from "./useChat";

interface ChatComposerProps {
  input: string;
  setInput: (v: string) => void;
  onSend: () => void;
  onStop: () => void;
  busy: boolean;
  turns: LocalChatMessage[];
}

export const ChatComposer = memo(({ input, setInput, onSend, onStop, busy, turns }: ChatComposerProps) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [showWarning, setShowWarning] = useState(false);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 192)}px`;
    }
  }, [input]);

  let placeholderText = "Message Browser MCP...";
  let currentAction = "";
  if (busy && turns.length > 0) {
    const lastTurn = turns[turns.length - 1];
    if (lastTurn.role === "tool" || lastTurn.role === "progress" || lastTurn.role === "workflow") {
      placeholderText = "Running browser automation...";
      if (lastTurn.role === "progress" && (lastTurn as any).step) {
          currentAction = (lastTurn as any).step;
      }
    } else {
      placeholderText = "Thinking...";
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (busy) {
        setShowWarning(true);
        setTimeout(() => setShowWarning(false), 3000);
        return;
      }
      onSend();
    }
  };

  return (
    <div className="chat-compose-container">
      {showWarning && (
        <div className="busy-warning fade-in">
          <Icon name="logs" style={{ width: "1rem", height: "1rem" }} />
          <span>
            {currentAction ? `Current step: ${currentAction}. ` : ""}
            Please wait until the current browser task finishes.
          </span>
        </div>
      )}
      <div className={`chat-compose-inner ${busy ? "is-busy" : ""}`}>
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          rows={1}
          value={input}
          disabled={busy}
          placeholder={placeholderText}
          aria-label="Message input"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        {busy ? (
          <button type="button" className="chat-stop-button" onClick={onStop} aria-label="Stop generation">
            <Icon name="moon" style={{ width: "1rem", height: "1rem" }} />
          </button>
        ) : (
          <button
            type="button"
            className="chat-send-button"
            disabled={!input.trim()}
            onClick={onSend}
            aria-label="Send message"
          >
            <Icon name="play" style={{ width: "1.2rem", height: "1.2rem" }} />
          </button>
        )}
      </div>
    </div>
  );
});
