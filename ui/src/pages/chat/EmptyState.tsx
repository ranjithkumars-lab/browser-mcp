import { memo } from "react";
import { Icon } from "../../components/Icon";

export const EmptyState = memo(({ onPrompt }: { onPrompt: (p: string) => void }) => {
  return (
    <div className="state slide-up" style={{ marginTop: "10vh" }}>
      <div className="state-icon">
        <Icon name="sun" style={{ width: "1.5rem", height: "1.5rem" }} />
      </div>
      <div className="state-title">Browser MCP Control Center</div>
      <div className="state-sub">
        Interact with your browser agent. Ask it to navigate pages, take snapshots, 
        extract data, or perform UI automation.
      </div>
      <div style={{ display: "flex", gap: "1rem", marginTop: "2rem", flexWrap: "wrap", justifyContent: "center" }}>
         <button className="btn btn-secondary" onClick={() => onPrompt("Go to example.com and take a screenshot")}>
           <Icon name="play" style={{ width: "1rem", height: "1rem" }} /> Screenshot Example.com
         </button>
         <button className="btn btn-secondary" onClick={() => onPrompt("Search Hacker News for the top story")}>
           <Icon name="play" style={{ width: "1rem", height: "1rem" }} /> Read Hacker News
         </button>
      </div>
    </div>
  );
});
