import { memo } from "react";
import { Icon } from "../../components/Icon";
import { useDisplayMode } from "./DisplayModeContext";

interface ChatToolbarProps {
  modelName: string;
  onOpenSettings: () => void;
}

export const ChatToolbar = memo(({ modelName, onOpenSettings }: ChatToolbarProps) => {
  const { mode, setMode } = useDisplayMode();

  return (
    <div className="chat-toolbar">
      <div className="model-badge">
         Model: <span className="badge badge-muted">{modelName || "Default"}</span>
      </div>
      <div className="chat-toolbar-modes">
        <button 
           className={`badge ${mode === "simple" ? "badge-primary" : "badge-muted"}`} 
           onClick={() => setMode("simple")}
           title="Simple: Answer, Screenshots, Downloads"
        >Simple</button>
        <button 
           className={`badge ${mode === "developer" ? "badge-primary" : "badge-muted"}`} 
           onClick={() => setMode("developer")}
           title="Developer: Raw JSON & Tool Calls"
        >Developer</button>
      </div>
      <button className="icon-btn" onClick={onOpenSettings} aria-label="Open settings">
         <Icon name="settings" style={{ width: "1.2rem", height: "1.2rem" }} />
      </button>
    </div>
  );
});
