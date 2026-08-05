"""Parameter Resolver for tracking and injecting execution context."""

from __future__ import annotations

import json
from typing import Any, cast
import structlog

from browser_mcp.api.chat.schemas import ChatMessage

_LOGGER = structlog.get_logger("browser_mcp.api.chat.resolver")


class ExecutionContext:
    """Tracks the active browser execution context across a conversation."""

    def __init__(self) -> None:
        self.session_id: str | None = None
        self.context_id: str | None = None
        self.page_id: str | None = None
        self.last_artifact: str | None = None
        self.last_navigation: str | None = None
        self.active_tab: str | None = None
        self.current_url: str | None = None

    @classmethod
    def from_messages(cls, messages: list[ChatMessage]) -> ExecutionContext:
        """Reconstruct the execution context by replaying the conversation history."""
        ctx = cls()
        
        for msg in messages:
            if msg.role == "tool" and getattr(msg, "name", None):
                name = getattr(msg, "name")
                content_str = getattr(msg, "content", "")
                
                try:
                    result = json.loads(content_str)
                    if isinstance(result, dict):
                        if name == "browser.create_session":
                            ctx.session_id = result.get("session_id", ctx.session_id)
                        elif name == "browser.create_context":
                            ctx.context_id = result.get("context_id", ctx.context_id)
                        elif name == "browser.new_page":
                            ctx.page_id = result.get("page_id", ctx.page_id)
                            ctx.active_tab = ctx.page_id
                        elif name == "browser.navigate":
                            ctx.last_navigation = result.get("url", ctx.last_navigation)
                            ctx.current_url = ctx.last_navigation
                        
                        # Fallback heuristic: any tool that returns these IDs updates the context
                        if "session_id" in result:
                            ctx.session_id = result["session_id"]
                        if "context_id" in result:
                            ctx.context_id = result["context_id"]
                        if "page_id" in result:
                            ctx.page_id = result["page_id"]
                            ctx.active_tab = ctx.page_id
                except (TypeError, ValueError):
                    pass
            
            elif msg.role == "artifact":
                ctx.last_artifact = getattr(msg, "artifact_id", ctx.last_artifact)

        return ctx

    def update_from_result(self, tool_name: str, result: Any) -> None:
        """Update context from a live tool result during stream."""
        if not isinstance(result, dict):
            return
        
        if tool_name == "browser.create_session":
            self.session_id = result.get("session_id", self.session_id)
        elif tool_name == "browser.create_context":
            self.context_id = result.get("context_id", self.context_id)
        elif tool_name == "browser.new_page":
            self.page_id = result.get("page_id", self.page_id)
            self.active_tab = self.page_id
        elif tool_name == "browser.navigate":
            self.last_navigation = result.get("url", self.last_navigation)
            self.current_url = self.last_navigation
            
        if "session_id" in result:
            self.session_id = result["session_id"]
        if "context_id" in result:
            self.context_id = result["context_id"]
        if "page_id" in result:
            self.page_id = result["page_id"]
            self.active_tab = self.page_id


class ParameterResolver:
    """Injects missing required parameters into tool calls using the ExecutionContext."""
    
    def __init__(self, context: ExecutionContext):
        self.context = context
        
    def resolve(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Inject missing session/context/page IDs into the arguments if required."""
        resolved = dict(arguments)
        
        # Tools that require session_id
        if tool_name.startswith("browser.") and tool_name != "browser.create_session":
            if "session_id" not in resolved or not resolved["session_id"]:
                if self.context.session_id:
                    resolved["session_id"] = self.context.session_id
                    _LOGGER.info("injected_parameter", parameter="session_id", tool=tool_name)
                else:
                    raise ValueError("Cannot execute browser task: no active browser session. Please start a session first.")
                    
        # Tools that require context_id
        if tool_name in ("browser.new_page", "browser.close_context"):
            if "context_id" not in resolved or not resolved["context_id"]:
                if self.context.context_id:
                    resolved["context_id"] = self.context.context_id
                    _LOGGER.info("injected_parameter", parameter="context_id", tool=tool_name)
                    
        # Tools that require page_id
        if tool_name in (
            "browser.navigate", 
            "browser.screenshot", 
            "browser.screenshot.full_page", 
            "browser.automation.execute"
        ) or tool_name.startswith("browser.action."):
            if "page_id" not in resolved or not resolved["page_id"]:
                if self.context.page_id:
                    resolved["page_id"] = self.context.page_id
                    _LOGGER.info("injected_parameter", parameter="page_id", tool=tool_name)
                    
        return resolved
