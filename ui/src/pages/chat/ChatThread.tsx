import { memo, useRef, useEffect, UIEvent, useState } from "react";
import { Icon } from "../../components/Icon";
import { MessageRenderer } from "./MessageRenderer";
import { EmptyState } from "./EmptyState";
import { AutomationTimeline } from "./AutomationTimeline";
import type { ProgressMessage, StatusMessage, ToolMessage } from "./types";
import { LocalChatMessage } from "./useChat";

interface ChatThreadProps {
  turns: LocalChatMessage[];
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

  // Group timeline events
  const renderedElements: React.ReactNode[] = [];
  let currentTimelineGroup: (ProgressMessage | StatusMessage | ToolMessage)[] = [];

  const flushTimeline = (keyPrefix: string) => {
    if (currentTimelineGroup.length > 0) {
      renderedElements.push(
        <AutomationTimeline key={`timeline-${keyPrefix}`} events={currentTimelineGroup} />
      );
      currentTimelineGroup = [];
    }
  };

  turns.forEach((turn, index) => {
    if (turn.role === "progress" || turn.role === "status" || turn.role === "tool") {
      currentTimelineGroup.push(turn as any);
    } else {
      flushTimeline(String(index));
      renderedElements.push(
        <MessageRenderer key={`msg-${index}`} turn={turn} isLast={index === turns.length - 1} />
      );
    }
  });
  flushTimeline("end");

  return (
    <div className="chat-main" style={{ position: "relative" }}>
      <div className="chat-thread" aria-live="polite" ref={threadRef} onScroll={handleScroll}>
        {renderedElements}
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
