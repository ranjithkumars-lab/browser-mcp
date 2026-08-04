"""Production-grade acceptance tests for the browser MCP toolkit.

Twenty acceptance tests that exercise the MCP tools exactly the way a client
invokes them — through the :class:`ToolRegistry` — against the fake Playwright
runtime. The suite is split into ten **simple** tests (single tool, happy
path) and ten **complex** tests (multi-step agent workflows that mirror how an
LLM would actually use the browser: login flows, form submission, keyboard
input, navigation, scraping and screenshots).

These tests pin the behaviour that was previously missing and caused agent
loops to stall: typing into fields (``browser.element.fill`` /
``browser.element.type``), submitting with ``Enter`` (``browser.element.press``
/ ``browser.keyboard.press``), clearing inputs, selecting options, checking
checkboxes, reading input values back, and the page-level keyboard tools.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from tests.fakes import FakeElement, FakeLocatorProvider, FakePage

from browser_mcp.browser.elements.state import ElementState
from browser_mcp.browser.screenshot import ScreenshotManager
from browser_mcp.plugins.forms.actions import FormActions
from browser_mcp.plugins.forms.detector import FormDetector
from browser_mcp.plugins.forms.tools import FormToolkit
from browser_mcp.plugins.forms.validator import FormValidator
from browser_mcp.plugins.scraper.actions import ScraperActions
from browser_mcp.plugins.scraper.tools import ScraperToolkit
from browser_mcp.tools.elements import ElementToolkit
from browser_mcp.tools.keyboard import KeyboardToolkit
from browser_mcp.tools.navigation import NavigationToolkit
from browser_mcp.tools.screenshot import ScreenshotToolkit
from enterprise_mcp.tools.registry import ToolRegistry
from enterprise_mcp.utils.errors import ToolError

pytestmark = pytest.mark.unit

PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a"
    "0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


class TextPage(FakePage):
    """FakePage whose ``evaluate`` returns body-text data for the scraper."""

    def __init__(self, body: str = "Login to Frappe") -> None:
        super().__init__(url="https://dev.example/", title="Login")
        self._body = body

    async def evaluate(self, expression: str, arg: Any = None) -> Any:
        if "innerText" in expression and arg is None:
            text = self._body
            return {
                "text": text,
                "word_count": len(text.split()),
                "char_count": len(text),
            }
        return await super().evaluate(expression, arg)


async def _build_env(tmp_path: Path, *, page: FakePage | None = None) -> dict[str, Any]:
    """Wire every toolkit into a shared registry around a fake runtime."""
    from browser_mcp.config.models import BrowserSettings

    settings = BrowserSettings(screenshot={"directory": str(tmp_path)})
    runtime = await _build_runtime(settings=settings, page=page)
    registry = ToolRegistry()

    NavigationToolkit(
        runtime["navigation"],
        runtime["history"],
        runtime["frames"],
        runtime["windows"],
        runtime["interactions"],
        runtime["waiting"],
    ).register(registry)
    ElementToolkit(runtime["engine"]).register(registry)
    KeyboardToolkit(runtime["interactions"]).register(registry)
    ScreenshotToolkit(ScreenshotManager(runtime["state"], settings)).register(registry)
    ScraperToolkit(ScraperActions(runtime["state"], runtime["events"])).register(registry)

    provider = FakeLocatorProvider()
    element_state = ElementState(provider)
    form_actions = FormActions(
        FormDetector(provider), FormValidator(element_state), element_state, runtime["events"]
    )
    FormToolkit(form_actions, runtime["frames"].page_object).register(registry)

    runtime["registry"] = registry
    runtime["settings"] = settings
    return runtime


async def _build_runtime(settings: Any, *, page: FakePage | None) -> dict[str, Any]:
    from tests.helpers import build_runtime as _build

    return await _build(settings=settings, page=page)


def _page_id(runtime: dict[str, Any]) -> str:
    return runtime["page_handle"].page_id


def _sid(runtime: dict[str, Any]) -> str:
    return runtime["session_id"]


def _editable_input(runtime: dict[str, Any], selector: str) -> None:
    runtime["page"].set_elements(
        selector, [FakeElement(tag="input", editable=True, enabled=True, visible=True)]
    )


async def _find_element_id(
    runtime: dict[str, Any], strategy: str, value: str, **kwargs: Any
) -> str:
    result = await runtime["registry"].call(
        "browser.element.find",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        strategy=strategy,
        value=value,
        **kwargs,
    )
    assert result["success"] is True, result
    return result["element_id"]


# ---------------------------------------------------------------------------
# SIMPLE TESTS — one tool, one happy path (10)
# ---------------------------------------------------------------------------


async def test_simple_goto(tmp_path: Path) -> None:
    runtime = await _build_env(tmp_path)
    result = await runtime["registry"].call(
        "browser.goto",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        url="https://example.com/",
    )
    assert result["success"] is True
    assert result["url"] == "https://example.com/"


async def test_simple_element_find(tmp_path: Path) -> None:
    runtime = await _build_env(tmp_path)
    result = await runtime["registry"].call(
        "browser.element.find",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        strategy="css",
        value="#login_email",
    )
    assert result["success"] is True
    assert result["element_id"].startswith("element_")
    assert result["count"] == 1


async def test_simple_element_text(tmp_path: Path) -> None:
    runtime = await _build_env(tmp_path)
    runtime["page"].set_elements("#heading", [FakeElement(text="Elements Fixture")])
    element_id = await _find_element_id(runtime, "css", "#heading")
    result = await runtime["registry"].call(
        "browser.element.text",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=element_id,
    )
    assert result["success"] is True
    assert result["text"] == "Elements Fixture"


async def test_simple_element_attribute(tmp_path: Path) -> None:
    runtime = await _build_env(tmp_path)
    runtime["page"].set_elements("#email", [FakeElement(attrs={"placeholder": "jane@example.com"})])
    element_id = await _find_element_id(runtime, "css", "#email")
    result = await runtime["registry"].call(
        "browser.element.attribute",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=element_id,
        attribute_name="placeholder",
    )
    assert result["success"] is True
    assert result["value"] == "jane@example.com"


async def test_simple_element_state(tmp_path: Path) -> None:
    runtime = await _build_env(tmp_path)
    runtime["page"].set_elements("#password", [FakeElement(editable=True, enabled=True)])
    element_id = await _find_element_id(runtime, "css", "#password")
    result = await runtime["registry"].call(
        "browser.element.state",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=element_id,
    )
    assert result["success"] is True
    assert result["exists"] is True
    assert result["editable"] is True


async def test_simple_element_fill_and_input_value(tmp_path: Path) -> None:
    runtime = await _build_env(tmp_path)
    _editable_input(runtime, "#email")
    element_id = await _find_element_id(runtime, "css", "#email")
    filled = await runtime["registry"].call(
        "browser.element.fill",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=element_id,
        value="Administrator",
    )
    assert filled["success"] is True
    assert filled["value"] == "Administrator"
    read_back = await runtime["registry"].call(
        "browser.element.input_value",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=element_id,
    )
    assert read_back["success"] is True
    assert read_back["value"] == "Administrator"


async def test_simple_element_press_enter(tmp_path: Path) -> None:
    runtime = await _build_env(tmp_path)
    _editable_input(runtime, "#email")
    element_id = await _find_element_id(runtime, "css", "#email")
    result = await runtime["registry"].call(
        "browser.element.press",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=element_id,
        key="Enter",
    )
    assert result["success"] is True
    assert result["key"] == "Enter"
    assert result["action"] == "press"


async def test_simple_element_clear(tmp_path: Path) -> None:
    runtime = await _build_env(tmp_path)
    _editable_input(runtime, "#search")
    element_id = await _find_element_id(runtime, "css", "#search")
    await runtime["registry"].call(
        "browser.element.fill",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=element_id,
        value="dust",
    )
    result = await runtime["registry"].call(
        "browser.element.clear",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=element_id,
    )
    assert result["success"] is True
    read_back = await runtime["registry"].call(
        "browser.element.input_value",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=element_id,
    )
    assert read_back["value"] == ""


async def test_simple_scrape_text(tmp_path: Path) -> None:
    runtime = await _build_env(tmp_path, page=TextPage(body="Login to Frappe"))
    result = await runtime["registry"].call(
        "browser.scrape.text",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        output_format="json",
    )
    assert result["success"] is True
    payload = json.loads(result["data"])
    assert payload[0]["word_count"] == 3
    assert "Frappe" in payload[0]["text"]


async def test_simple_screenshot(tmp_path: Path) -> None:
    runtime = await _build_env(tmp_path)
    runtime["page"].screenshot_bytes = PNG_1X1
    result = await runtime["registry"].call(
        "browser.screenshot",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
    )
    assert result["success"] is True
    assert result["format"] == "png"
    assert result["mime_type"] == "image/png"
    assert result["width"] == 1
    assert result["height"] == 1
    assert Path(result["screenshot_path"]).exists()


# ---------------------------------------------------------------------------
# COMPLEX TESTS — multi-step workflows an agent actually runs (10)
# ---------------------------------------------------------------------------


async def test_complex_login_flow_with_element_tools(tmp_path: Path) -> None:
    """Find email + password, fill both, press Enter to submit — the flow
    that previously stalled the agent because no typing tools existed."""
    runtime = await _build_env(tmp_path)
    _editable_input(runtime, "#login_email")
    _editable_input(runtime, "#login_password")

    email_id = await _find_element_id(runtime, "css", "#login_email")
    password_id = await _find_element_id(runtime, "css", "#login_password")

    await runtime["registry"].call(
        "browser.element.fill",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=email_id,
        value="Administrator",
    )
    await runtime["registry"].call(
        "browser.element.fill",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=password_id,
        value="CSSAAPV@24",
    )
    submitted = await runtime["registry"].call(
        "browser.element.press",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=password_id,
        key="Enter",
    )

    email = await runtime["registry"].call(
        "browser.element.input_value",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=email_id,
    )
    password = await runtime["registry"].call(
        "browser.element.input_value",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=password_id,
    )
    assert submitted["success"] is True
    assert email["value"] == "Administrator"
    assert password["value"] == "CSSAAPV@24"


async def test_complex_keyboard_type_and_press(tmp_path: Path) -> None:
    runtime = await _build_env(tmp_path)
    result = await runtime["registry"].call(
        "browser.keyboard.type",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        text="Administrator",
    )
    assert result["success"] is True
    pressed = await runtime["registry"].call(
        "browser.keyboard.press",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        key="Enter",
    )
    assert pressed["success"] is True
    assert pressed["key"] == "Enter"
    assert runtime["page"].keyboard.typed == ["Administrator"]
    assert runtime["page"].keyboard.pressed == ["Enter"]


async def test_complex_checkbox_and_select_flow(tmp_path: Path) -> None:
    runtime = await _build_env(tmp_path)
    runtime["page"].set_elements(
        "#remember",
        [FakeElement(tag="input", enabled=True, editable=False, visible=True)],
    )
    runtime["page"].set_elements(
        "#role",
        [FakeElement(tag="select", enabled=True, editable=True, visible=True)],
    )

    checkbox_id = await _find_element_id(runtime, "css", "#remember")
    select_id = await _find_element_id(runtime, "css", "#role")

    checked = await runtime["registry"].call(
        "browser.element.check",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=checkbox_id,
    )
    assert checked["success"] is True

    state = await runtime["registry"].call(
        "browser.element.state",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=checkbox_id,
    )
    assert state["checked"] is True

    selected = await runtime["registry"].call(
        "browser.element.select_option",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=select_id,
        value="admin",
    )
    assert selected["success"] is True

    uncheck = await runtime["registry"].call(
        "browser.element.uncheck",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=checkbox_id,
    )
    assert uncheck["success"] is True
    state_after = await runtime["registry"].call(
        "browser.element.state",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=checkbox_id,
    )
    assert state_after["checked"] is False


async def test_complex_form_plugin_fill_and_submit(tmp_path: Path) -> None:
    runtime = await _build_env(tmp_path)
    _editable_input(runtime, "#email")
    _editable_input(runtime, "#password")

    filled = await runtime["registry"].call(
        "browser.form.fill",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        field="email",
        value="Administrator",
    )
    assert filled["success"] is True, filled
    filled_pw = await runtime["registry"].call(
        "browser.form.fill",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        field="password",
        value="CSSAAPV@24",
    )
    assert filled_pw["success"] is True
    submitted = await runtime["registry"].call(
        "browser.form.submit",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
    )
    assert submitted["success"] is True
    assert runtime["page"].locator("#email").filled == ["Administrator"]


async def test_complex_multi_step_navigation(tmp_path: Path) -> None:
    runtime = await _build_env(tmp_path)
    steps: list[str] = []

    gone = await runtime["registry"].call(
        "browser.goto",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        url="https://example.com/",
    )
    steps.append("goto")
    assert gone["success"] is True

    waited = await runtime["registry"].call(
        "browser.wait_url",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        pattern="**/",
    )
    steps.append("wait_url")
    assert waited["success"] is True

    scrolled = await runtime["registry"].call(
        "browser.scroll_by",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        delta_x=0,
        delta_y=200,
    )
    steps.append("scroll")
    assert scrolled["success"] is True

    clicked = await runtime["registry"].call(
        "browser.click",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        selector="#cta",
    )
    steps.append("click")
    assert clicked["success"] is True

    listed = await runtime["registry"].call(
        "browser.list_windows",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
    )
    steps.append("list_windows")
    assert listed["success"] is True
    assert steps == ["goto", "wait_url", "scroll", "click", "list_windows"]


async def test_complex_find_all_then_interact(tmp_path: Path) -> None:
    runtime = await _build_env(tmp_path)
    runtime["page"].set_elements("li.item", [FakeElement(text="first"), FakeElement(text="second")])
    found = await runtime["registry"].call(
        "browser.element.find_all",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        strategy="css",
        value="li.item",
    )
    assert found["success"] is True
    assert found["count"] == 2
    first_id = found["elements"][0]["element_id"]
    second_id = found["elements"][1]["element_id"]

    text = await runtime["registry"].call(
        "browser.element.text",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=second_id,
    )
    assert text["text"] == "second"

    clicked = await runtime["registry"].call(
        "browser.click",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=first_id,
    )
    assert clicked["success"] is True
    assert clicked["element_id"] == first_id


async def test_complex_error_hints_then_recovery(tmp_path: Path) -> None:
    runtime = await _build_env(tmp_path)
    runtime["page"].set_elements("input[name='login']", [])
    failed = await runtime["registry"].call(
        "browser.element.find",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        strategy="css",
        value="input[name='login']",
    )
    assert failed["success"] is False
    assert "not found" in failed["error"]
    assert "Hint:" in failed["error"]
    assert "browser.form.fill" in failed["error"]

    _editable_input(runtime, "#login_email")
    recovered = await _find_element_id(runtime, "css", "#login_email")
    assert recovered.startswith("element_")


async def test_complex_type_with_delay_and_readback(tmp_path: Path) -> None:
    runtime = await _build_env(tmp_path)
    _editable_input(runtime, "#autocomplete")
    element_id = await _find_element_id(runtime, "css", "#autocomplete")
    result = await runtime["registry"].call(
        "browser.element.type",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=element_id,
        text="amr",
        delay_ms=5,
    )
    assert result["success"] is True
    assert result["action"] == "type"
    assert result["delay_ms"] == 5
    read_back = await runtime["registry"].call(
        "browser.element.input_value",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=element_id,
    )
    assert read_back["value"] == "amr"


async def test_complex_end_to_end_agent_workflow(tmp_path: Path) -> None:
    """A full agent-style session: scrape to inspect, find fields, fill,
    press Enter, wait for navigation, screenshot the result."""
    runtime = await _build_env(tmp_path, page=TextPage(body="Login to Frappe"))
    _editable_input(runtime, "#login_email")
    _editable_input(runtime, "#login_password")

    scraped = await runtime["registry"].call(
        "browser.scrape.text",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        output_format="json",
    )
    assert scraped["success"] is True

    email_id = await _find_element_id(runtime, "css", "#login_email")
    password_id = await _find_element_id(runtime, "css", "#login_password")
    await runtime["registry"].call(
        "browser.element.fill",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=email_id,
        value="Administrator",
    )
    await runtime["registry"].call(
        "browser.element.fill",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=password_id,
        value="CSSAAPV@24",
    )
    await runtime["registry"].call(
        "browser.keyboard.press",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        key="Enter",
    )
    runtime["page"].screenshot_bytes = PNG_1X1
    shot = await runtime["registry"].call(
        "browser.screenshot",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
    )
    assert shot["success"] is True
    assert Path(shot["screenshot_path"]).exists()


async def test_complex_unknown_tool_and_underscore_alias(tmp_path: Path) -> None:
    runtime = await _build_env(tmp_path)
    with pytest.raises(ToolError):
        await runtime["registry"].call("browser.element_send_keys")  # agent-guessed name

    _editable_input(runtime, "#email")
    aliased = await runtime["registry"].call(
        "browser.element_fill",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        element_id=await _find_element_id(runtime, "css", "#email"),
        value="via-alias",
    )
    assert aliased["success"] is True

    keyboard_aliased = await runtime["registry"].call(
        "browser.keyboard_press",
        session_id=_sid(runtime),
        page_id=_page_id(runtime),
        key="Enter",
    )
    assert keyboard_aliased["success"] is True
