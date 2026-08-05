import { memo } from "react";
import { Icon } from "../../components/Icon";

interface ChatToolbarProps {
  modelName: string;
  onOpenSettings: () => void;
}

export const ChatToolbar = memo(({ modelName, onOpenSettings }: ChatToolbarProps) => {
  return (
    <div className="chat-toolbar">
      <div className="model-badge">
         Model: <span className="badge badge-muted">{modelName || "Default"}</span>
      </div>
      <button className="icon-btn" onClick={onOpenSettings} aria-label="Open settings">
         <Icon name="settings" style={{ width: "1.2rem", height: "1.2rem" }} />
      </button>
    </div>
  );
});
