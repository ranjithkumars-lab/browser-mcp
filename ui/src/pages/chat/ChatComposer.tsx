import { memo, KeyboardEvent, useRef, useEffect } from "react";
import { Icon } from "../../components/Icon";

interface ChatComposerProps {
  input: string;
  setInput: (v: string) => void;
  onSend: () => void;
  onStop: () => void;
  busy: boolean;
}

export const ChatComposer = memo(({ input, setInput, onSend, onStop, busy }: ChatComposerProps) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 192)}px`;
    }
  }, [input]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="chat-compose-container">
      <div className="chat-compose-inner">
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          rows={1}
          value={input}
          placeholder="Message Browser MCP..."
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
