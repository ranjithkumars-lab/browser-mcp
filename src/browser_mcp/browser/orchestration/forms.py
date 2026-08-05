"""Deterministic Form Engine for finding and interacting with forms."""

import asyncio
from typing import Any
from browser_mcp.browser.elements.engine import ElementEngine
import structlog

_LOGGER = structlog.get_logger("browser_mcp.browser.orchestration.forms")

class FormEngine:
    """Handles deterministic discovery and filling of form fields."""
    
    def __init__(self, element_engine: ElementEngine):
        self._engine = element_engine

    async def fill_and_submit(self, session_id: str, page_id: str, fields: dict[str, Any]) -> None:
        """Fill all fields and submit the form."""
        _LOGGER.info("form_engine_start_fill", fields=list(fields.keys()))
        
        # Sequentially fill fields to allow dependent dropdowns to resolve
        for key, value in fields.items():
            await self._fill_field(session_id, page_id, key, value)
            # Give the DOM time to mutate in case this was a dependent dropdown
            await asyncio.sleep(1)
            
        await self._submit_form(session_id, page_id)

    async def _fill_field(self, session_id: str, page_id: str, label_or_name: str, value: Any) -> None:
        """Heuristically find a field by label, name, or placeholder and fill it."""
        try:
            # 1. Try to find by explicit Label text
            result = await self._engine.find(session_id, page_id, "text", label_or_name, timeout_ms=3000, strict=False)
            element_id = result["element_id"]
            
            # Usually the label text is associated with an input or is near it
            # To be simple for now, we try aria role search
        except Exception:
            try:
                # 2. Try by placeholder or name attribute via css
                css_selector = f"input[name='{label_or_name}'], input[placeholder*='{label_or_name}'], select[name='{label_or_name}']"
                result = await self._engine.find(session_id, page_id, "css", css_selector, timeout_ms=3000, strict=False)
                element_id = result["element_id"]
            except Exception as e:
                _LOGGER.warning("form_engine_field_not_found", field=label_or_name, error=str(e))
                return

        # Determine type of element
        try:
            # If it's a select, use select_option, else fill
            html = await self._engine.html(session_id, page_id, element_id, outer=True)
            if "<select" in str(html.get("html", "")).lower():
                await self._engine.select_option(session_id, page_id, element_id, str(value))
            else:
                await self._engine.fill(session_id, page_id, element_id, str(value))
        except Exception as e:
            _LOGGER.error("form_engine_field_fill_failed", field=label_or_name, error=str(e))

    async def _submit_form(self, session_id: str, page_id: str) -> None:
        """Find a submit button and click it."""
        try:
            # Look for button[type="submit"] or text "Login", "Submit", "Sign In"
            result = await self._engine.find(session_id, page_id, "css", "button[type='submit'], input[type='submit'], button:has-text('Login'), button:has-text('Submit')", timeout_ms=2000, strict=False)
            await self._engine.click(session_id, page_id, result["element_id"])
        except Exception as e:
            _LOGGER.warning("form_engine_submit_failed", error=str(e))
            # Fallback to pressing Enter on the page
            try:
                # Find body and press enter
                body = await self._engine.find(session_id, page_id, "css", "body", strict=False)
                await self._engine.press(session_id, page_id, body["element_id"], "Enter")
            except Exception:
                pass
