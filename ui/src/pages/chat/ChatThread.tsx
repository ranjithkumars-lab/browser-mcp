import { memo, useRef, useEffect, UIEvent, useState } from "react";
import { Icon } from "../../components/Icon";
import { MessageRenderer } from "./MessageRenderer";
import { EmptyState } from "./EmptyState";
import type { Turn } from "./types";

interface ChatThreadProps {
  turns: Turn[];
  busy: boolean;
  onPrompt: (prompt: string) => void;
}

export const ChatThread = memo(({ turns, busy, onPrompt }: ChatThreadProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const threadRef = useRef<HTMLDivElement>(null);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const isAutoScrolling = useRef(true);

  const scrollToBottom = () => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
    isAutoScrolling.current = true;
    setShowScrollBtn(false);
  };

  useEffect(() => {
    if (isAutoScrolling.current) {
      scrollRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [turns, busy]);

  const handleScroll = (e: UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    const isAtBottom = target.scrollHeight - target.scrollTop <= target.clientHeight + 80;
    isAutoScrolling.current = isAtBottom;
    setShowScrollBtn(!isAtBottom);
  };

  if (turns.length === 0 && !busy) {
    return (
      <div className="chat-thread">
        <EmptyState onPrompt={onPrompt} />
      </div>
    );
  }

  return (
    <div className="chat-main" style={{ position: "relative" }}>
      <div className="chat-thread" aria-live="polite" ref={threadRef} onScroll={handleScroll}>
        {turns.map((turn, index) => (
          <MessageRenderer key={index} turn={turn} isLast={index === turns.length - 1} />
        ))}
        <div ref={scrollRef} style={{ height: "1px" }} />
      </div>
      
      {showScrollBtn && (
        <button className="scroll-to-latest fade-in" onClick={scrollToBottom}>
          <Icon name="moon" style={{ width: "1rem", height: "1rem", transform: "rotate(90deg)" }} />
          Jump to latest
        </button>
      )}
    </div>
  );
});
