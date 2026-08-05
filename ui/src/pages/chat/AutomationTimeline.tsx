import React, { useState } from "react";
import { ProgressMessage, StatusMessage, ToolMessage, WorkflowMessage } from "./types";
import { Icon } from "../../components/Icon";
import { useDisplayMode } from "./DisplayModeContext";

interface AutomationTimelineProps {
  events: (ProgressMessage | StatusMessage | ToolMessage | WorkflowMessage)[];
}

export const AutomationTimeline: React.FC<AutomationTimelineProps> = ({ events }) => {
  const [collapsed, setCollapsed] = useState(true);
  const { mode } = useDisplayMode();

  if (events.length === 0) return null;
  
  // Only show in advanced and developer modes
  if (mode === "simple") return null;

  const runningCount = events.filter(e => (e.role === "progress" || e.role === "workflow") && e.status === "running").length;
  const errorCount = events.filter(e => (e.role === "progress" || e.role === "workflow") && e.status === "failed").length;
  const isRunning = runningCount > 0;
  
  return (
    <div className="chat-message-wrapper assistant slide-up" style={{ padding: "0.25rem var(--space-5)" }}>
      <div className="chat-message">
        <div className="chat-avatar" style={{background: "transparent"}} />
        <div className="chat-message-content" style={{ maxWidth: "100%" }}>
          <div style={{ background: "var(--surface-2)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", fontSize: "var(--text-sm)" }}>
            <div 
               style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0.75rem 1rem", cursor: "pointer", userSelect: "none" }}
               onClick={() => setCollapsed(!collapsed)}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontWeight: 600, color: "var(--text)" }}>
                <Icon name="jobs" style={{ width: "1.1rem", height: "1.1rem", color: errorCount > 0 ? "red" : isRunning ? "var(--accent)" : "var(--success)" }} />
                <span>Automation Timeline ({events.length} events)</span>
                {isRunning && <span className="badge badge-primary" style={{ padding: "0.1rem 0.4rem", fontSize: "0.7rem", animation: "pulse 2s infinite" }}>Running</span>}
              </div>
              <Icon name="menu" style={{ width: "1rem", height: "1rem", transform: collapsed ? "rotate(0deg)" : "rotate(180deg)", transition: "transform 0.2s" }} />
            </div>
            
            {!collapsed && (
              <div style={{ padding: "0 1rem 1rem 1rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                {events.map((event, index) => {
                  let label = "";
                  let statusColor = "var(--text-secondary)";

                  if (event.role === "progress") {
                    label = event.step;
                    if (event.status === "running") statusColor = "var(--accent)";
                    if (event.status === "success") statusColor = "var(--success)";
                    if (event.status === "failed") statusColor = "red";
                  } else if (event.role === "status") {
                    label = event.content;
                  } else if (event.role === "tool") {
                    label = `Tool: ${event.name}`;
                    statusColor = "var(--muted)";
                  } else if (event.role === "workflow") {
                     label = `Workflow [${event.workflow_type}]: ${event.status}`;
                     if (event.status === "running") statusColor = "var(--accent)";
                     if (event.status === "success") statusColor = "var(--success)";
                     if (event.status === "failed") statusColor = "red";
                  }

                  return (
                    <div key={index} style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start", position: "relative", paddingLeft: "1.5rem" }}>
                      <div style={{ position: "absolute", left: "0.25rem", top: "0.3rem", width: "0.5rem", height: "0.5rem", borderRadius: "50%", background: statusColor }} />
                      <div style={{ display: "flex", flexDirection: "column" }}>
                        <span style={{ color: "var(--text)", fontWeight: 500 }}>{label}</span>
                        {(event.role === "progress" || event.role === "workflow") && event.details && (
                          <span style={{ color: "var(--text-secondary)", fontSize: "var(--text-xs)", marginTop: "0.1rem" }}>{event.details}</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
