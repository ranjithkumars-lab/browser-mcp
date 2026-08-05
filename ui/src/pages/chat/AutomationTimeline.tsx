import React from "react";
import { ProgressMessage, StatusMessage, ToolMessage } from "./types";
import Icon from "../../components/Icon";

interface AutomationTimelineProps {
  events: (ProgressMessage | StatusMessage | ToolMessage)[];
}

export const AutomationTimeline: React.FC<AutomationTimelineProps> = ({ events }) => {
  if (events.length === 0) return null;

  return (
    <div className="flex flex-col gap-2 p-4 bg-gray-50 border border-gray-200 rounded-lg text-sm mb-4">
      <div className="font-semibold text-gray-700 flex items-center gap-2 mb-2">
        <Icon name="Activity" className="w-4 h-4 text-blue-500" />
        Automation Progress
      </div>
      <div className="flex flex-col gap-3 relative pl-4 border-l border-gray-300 ml-2">
        {events.map((event, index) => {
          let label = "";
          let statusIcon = null;

          if (event.role === "progress") {
            label = event.step;
            if (event.status === "running") {
              statusIcon = <div className="absolute -left-1.5 w-3 h-3 bg-blue-500 rounded-full animate-pulse" />;
            } else if (event.status === "success") {
              statusIcon = <div className="absolute -left-1.5 w-3 h-3 bg-green-500 rounded-full" />;
            } else if (event.status === "failed") {
              statusIcon = <div className="absolute -left-1.5 w-3 h-3 bg-red-500 rounded-full" />;
            }
          } else if (event.role === "status") {
            label = event.content;
            statusIcon = <div className="absolute -left-1.5 w-3 h-3 bg-gray-400 rounded-full" />;
          } else if (event.role === "tool") {
            label = `Executing: ${event.name}`;
            statusIcon = <div className="absolute -left-1.5 w-3 h-3 bg-yellow-500 rounded-full" />;
          }

          return (
            <div key={index} className="flex items-center gap-3 relative">
              {statusIcon}
              <span className="text-gray-600 font-medium">{label}</span>
              {event.role === "progress" && event.details && (
                <span className="text-gray-400 text-xs truncate max-w-[200px]">{event.details}</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
