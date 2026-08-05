"""Prompt management architecture for the Ollama chat agent."""

from __future__ import annotations

from typing import Any

class PromptManager:
    """Orchestrates the assembly of system context and user rules."""
    
    def __init__(self, chat_config: Any) -> None:
        self._chat_config = chat_config
        self._system_builder = SystemPromptBuilder()
        self._style_policy = ResponseStylePolicy(chat_config.response_style)
        
    def build_system_prompt(self) -> str:
        """Combine all rules into the final system prompt."""
        parts = [
            self._system_builder.build(),
            self._style_policy.build(),
        ]
        return "\n\n".join(filter(None, parts))


class SystemPromptBuilder:
    """Generates the baseline browser operation rules."""
    
    def build(self) -> str:
        return (
            "You are a helpful assistant operating a browser through MCP tools. "
            "Only call browser tools when the user explicitly asks you to browse, "
            "inspect, or interact with a web page. For greetings, general questions, "
            "or anything that does not require browsing, reply directly without "
            "calling any tools.\n"
            "To work on a web page:\n"
            "1. Call browser.create_session\n"
            "2. Call browser.create_context (on the returned session_id)\n"
            "3. Call browser.new_page (with that context_id; optionally pass a url)\n"
            "Reuse the exact session_id/context_id/page_id returned by the tools in "
            "every later call.\n\n"
            "CRITICAL: If a task requires multiple steps, prefer high-level orchestration "
            "tools (like browser.automation.execute) over manual DOM inspection. "
            "The assistant must never expose internal implementation details, filesystem paths, "
            "API payloads, or tool-specific identifiers to end users. "
            "Presentation is handled entirely by the structured message pipeline."
        )


class ResponseStylePolicy:
    """Enforces the conversational style."""
    
    def __init__(self, style: str) -> None:
        self.style = style

    def build(self) -> str:
        if self.style == "conversational":
            return (
                "RESPONSE RULES:\n"
                "- Maintain a natural conversation.\n"
                "- Do NOT use unnecessary headings like 'What the browser tools did'.\n"
                "- Do NOT repeat step-by-step tool actions to the user.\n"
                "- Focus directly on answering the user's request. Keep it strictly goal-centric.\n"
                "- For example, say 'Screenshot attached' or 'Login completed successfully' instead of logging execution details.\n"
                "- Keep responses concise; expand only when asked."
            )
        return ""
