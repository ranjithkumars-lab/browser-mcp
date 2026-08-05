"""Prompt management architecture for the Ollama chat agent."""

from __future__ import annotations

from typing import Any

class PromptManager:
    """Orchestrates the assembly of system context, user rules, and artifact formatting."""
    
    def __init__(self, chat_config: Any) -> None:
        self._chat_config = chat_config
        self._system_builder = SystemPromptBuilder()
        self._style_policy = ResponseStylePolicy(chat_config.response_style)
        self._artifact_formatter = ArtifactFormatter(chat_config.artifact_preview)
        
    def build_system_prompt(self) -> str:
        """Combine all rules into the final system prompt."""
        parts = [
            self._system_builder.build(),
            self._style_policy.build(),
            self._artifact_formatter.build()
        ]
        return "\n\n".join(filter(None, parts))

    def build_summary_prompt(self) -> dict[str, str]:
        """Generate a natural conversational prompt for ending a multi-step sequence."""
        return {
            "role": "user",
            "content": (
                "Continue. Provide a natural, conversational response based on the "
                "outcomes of the browser actions. "
                "Do not use generic headings. "
                "Keep it concise. Do not call any tools."
            )
        }


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
            "every later call. To read page content use browser.scrape.text with "
            "output_format 'markdown'. Do not invent tool names or IDs.\n\n"
            "CRITICAL: If a task requires multiple steps (like filling a form, clicking submit, "
            "and taking a screenshot), you MUST execute the tools sequentially until the entire "
            "task is complete. Do NOT stop halfway to tell the user what you plan to do next. "
            "Only stop and respond with text when the FINAL step (like the screenshot or download) "
            "has been successfully completed."
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
                "- Mention browser actions only when useful or relevant.\n"
                "- Focus directly on answering the user's request.\n"
                "- Keep responses concise; expand only when asked."
            )
        return ""


class ArtifactFormatter:
    """Instructs the LLM on how to cite artifact_ids."""
    
    def __init__(self, enable_preview: bool) -> None:
        self.enable_preview = enable_preview

    def build(self) -> str:
        if self.enable_preview:
            return (
                "ARTIFACT RENDERING:\n"
                "When a tool returns an `artifact_id` (e.g. for a screenshot or download), "
                "you MUST include a markdown image link in your text using the exact syntax:\n"
                "![Preview](artifact:<artifact_id>)\n"
                "For example: ![Preview](artifact:1234abcd)\n"
                "Do NOT output raw filesystem paths."
            )
        return ""
