"""Tests for the forms plugin."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from browser_mcp.errors import ElementNotFoundError, ElementStateError
from browser_mcp.plugins.forms.actions import FormActions, _make_result
from browser_mcp.plugins.forms.detector import FormDetector
from browser_mcp.plugins.forms.validator import FormValidator


class TestFormDetector:
    @pytest.mark.asyncio
    async def test_explicit_selector(self) -> None:
        detector = FormDetector(MagicMock())
        result = await detector.detect(MagicMock(), explicit_selector="#my-input")
        assert len(result) == 1
        assert result[0]["strategy"] == "css"
        assert result[0]["value"] == "#my-input"

    @pytest.mark.asyncio
    async def test_field_id(self) -> None:
        detector = FormDetector(MagicMock())
        result = await detector.detect(MagicMock(), field_id="my-id")
        assert any(c["value"] == "#my-id" for c in result)

    @pytest.mark.asyncio
    async def test_field_name(self) -> None:
        detector = FormDetector(MagicMock())
        result = await detector.detect(MagicMock(), field_name="username")
        assert any(c["value"] == '[name="username"]' for c in result)

    @pytest.mark.asyncio
    async def test_field_placeholder(self) -> None:
        detector = FormDetector(MagicMock())
        result = await detector.detect(
            MagicMock(), field_placeholder="Enter email"
        )
        assert any(
            '[placeholder="Enter email"]' in c["value"] for c in result
        )

    @pytest.mark.asyncio
    async def test_multiple_criteria(self) -> None:
        detector = FormDetector(MagicMock())
        result = await detector.detect(
            MagicMock(), field_id="email", field_name="email"
        )
        assert len(result) >= 2

    @pytest.mark.asyncio
    async def test_no_criteria_returns_empty(self) -> None:
        detector = FormDetector(MagicMock())
        result = await detector.detect(MagicMock())
        assert result == []


class TestFormValidator:
    @pytest.mark.asyncio
    async def test_validate_passes(self) -> None:
        state = MagicMock()
        state.snapshot = AsyncMock(
            return_value={
                "exists": True,
                "visible": True,
                "enabled": True,
                "editable": True,
                "checked": False,
            }
        )
        validator = FormValidator(state)
        result = await validator.validate(MagicMock())
        assert result["exists"] is True

    @pytest.mark.asyncio
    async def test_validate_raises_when_not_exists(self) -> None:
        state = MagicMock()
        state.snapshot = AsyncMock(
            return_value={
                "exists": False,
                "visible": False,
                "enabled": False,
                "editable": False,
                "checked": False,
            }
        )
        validator = FormValidator(state)
        with pytest.raises(ElementNotFoundError):
            await validator.validate(MagicMock())

    @pytest.mark.asyncio
    async def test_validate_requires_visible(self) -> None:
        state = MagicMock()
        state.snapshot = AsyncMock(
            return_value={
                "exists": True,
                "visible": False,
                "enabled": True,
                "editable": True,
                "checked": False,
            }
        )
        validator = FormValidator(state)
        with pytest.raises(ElementStateError):
            await validator.validate(MagicMock(), require_visible=True)

    @pytest.mark.asyncio
    async def test_validate_requires_enabled(self) -> None:
        state = MagicMock()
        state.snapshot = AsyncMock(
            return_value={
                "exists": True,
                "visible": True,
                "enabled": False,
                "editable": True,
                "checked": False,
            }
        )
        validator = FormValidator(state)
        with pytest.raises(ElementStateError):
            await validator.validate(MagicMock(), require_enabled=True)

    @pytest.mark.asyncio
    async def test_validate_requires_editable(self) -> None:
        state = MagicMock()
        state.snapshot = AsyncMock(
            return_value={
                "exists": True,
                "visible": True,
                "enabled": True,
                "editable": False,
                "checked": False,
            }
        )
        validator = FormValidator(state)
        with pytest.raises(ElementStateError):
            await validator.validate(MagicMock(), require_editable=True)


class TestMakeResult:
    def test_success_result(self) -> None:
        result = _make_result(
            success=True,
            session_id="s1",
            browser_id="b1",
            context_id="c1",
            page_id="p1",
            duration_ms=10,
            message="OK",
        )
        assert result["success"] is True
        assert result["session_id"] == "s1"
        assert result["message"] == "OK"
        assert "error" not in result

    def test_error_result(self) -> None:
        result = _make_result(
            success=False,
            session_id="s1",
            browser_id="b1",
            context_id="c1",
            page_id="p1",
            duration_ms=5,
            message="Failed",
            error="something went wrong",
        )
        assert result["success"] is False
        assert result["error"] == "something went wrong"


class TestFormActionsFill:
    @pytest.mark.asyncio
    async def test_fill_success(self) -> None:
        detector = MagicMock()
        detector.detect = AsyncMock(
            return_value=[{"strategy": "css", "value": "#name"}]
        )
        validator = MagicMock()
        validator.validate = AsyncMock(
            return_value={
                "exists": True,
                "visible": True,
                "enabled": True,
                "editable": True,
                "checked": False,
            }
        )
        state = MagicMock()
        event_bus = MagicMock()
        event_bus.publish = AsyncMock()

        actions = FormActions(detector, validator, state, event_bus)
        page = MagicMock()
        page.locator.return_value.fill = AsyncMock()

        result = await actions.fill(
            page=page,
            session_id="s1",
            browser_id="b1",
            context_id="c1",
            page_id="p1",
            field="name",
            value="John",
        )
        assert result["success"] is True
        assert "filled successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_fill_field_not_found(self) -> None:
        detector = MagicMock()
        detector.detect = AsyncMock(return_value=[])
        validator = MagicMock()
        event_bus = MagicMock()
        event_bus.publish = AsyncMock()
        state = MagicMock()

        actions = FormActions(detector, validator, state, event_bus)
        page = MagicMock()

        result = await actions.fill(
            page=page,
            session_id="s1",
            browser_id="b1",
            context_id="c1",
            page_id="p1",
            field="missing",
            value="value",
        )
        assert result["success"] is False
        assert "Could not resolve" in result["error"]


class TestFormActionsCheck:
    @pytest.mark.asyncio
    async def test_check_success(self) -> None:
        detector = MagicMock()
        detector.detect = AsyncMock(
            return_value=[{"strategy": "css", "value": "#agree"}]
        )
        validator = MagicMock()
        validator.validate = AsyncMock(
            return_value={
                "exists": True,
                "visible": True,
                "enabled": True,
                "editable": False,
                "checked": False,
            }
        )
        state = MagicMock()
        event_bus = MagicMock()
        event_bus.publish = AsyncMock()

        actions = FormActions(detector, validator, state, event_bus)
        page = MagicMock()
        page.locator.return_value.check = AsyncMock()

        result = await actions.check(
            page=page,
            session_id="s1",
            browser_id="b1",
            context_id="c1",
            page_id="p1",
            field="agree",
        )
        assert result["success"] is True


class TestFormActionsUncheck:
    @pytest.mark.asyncio
    async def test_uncheck_success(self) -> None:
        detector = MagicMock()
        detector.detect = AsyncMock(
            return_value=[{"strategy": "css", "value": "#agree"}]
        )
        validator = MagicMock()
        validator.validate = AsyncMock(
            return_value={
                "exists": True,
                "visible": True,
                "enabled": True,
                "editable": False,
                "checked": True,
            }
        )
        state = MagicMock()
        event_bus = MagicMock()
        event_bus.publish = AsyncMock()

        actions = FormActions(detector, validator, state, event_bus)
        page = MagicMock()
        page.locator.return_value.uncheck = AsyncMock()

        result = await actions.uncheck(
            page=page,
            session_id="s1",
            browser_id="b1",
            context_id="c1",
            page_id="p1",
            field="agree",
        )
        assert result["success"] is True


class TestFormActionsSelect:
    @pytest.mark.asyncio
    async def test_select_success(self) -> None:
        detector = MagicMock()
        detector.detect = AsyncMock(
            return_value=[{"strategy": "css", "value": "#country"}]
        )
        validator = MagicMock()
        validator.validate = AsyncMock(
            return_value={
                "exists": True,
                "visible": True,
                "enabled": True,
                "editable": False,
                "checked": False,
            }
        )
        state = MagicMock()
        event_bus = MagicMock()
        event_bus.publish = AsyncMock()

        actions = FormActions(detector, validator, state, event_bus)
        page = MagicMock()
        page.locator.return_value.select_option = AsyncMock()

        result = await actions.select(
            page=page,
            session_id="s1",
            browser_id="b1",
            context_id="c1",
            page_id="p1",
            field="country",
            value="us",
        )
        assert result["success"] is True


class TestFormActionsSubmit:
    @pytest.mark.asyncio
    async def test_submit_with_field(self) -> None:
        detector = MagicMock()
        detector.detect = AsyncMock(
            return_value=[{"strategy": "css", "value": "#submit-btn"}]
        )
        validator = MagicMock()
        validator.validate = AsyncMock(
            return_value={
                "exists": True,
                "visible": True,
                "enabled": True,
                "editable": False,
                "checked": False,
            }
        )
        state = MagicMock()
        event_bus = MagicMock()
        event_bus.publish = AsyncMock()

        actions = FormActions(detector, validator, state, event_bus)
        page = MagicMock()
        page.locator.return_value.click = AsyncMock()

        result = await actions.submit(
            page=page,
            session_id="s1",
            browser_id="b1",
            context_id="c1",
            page_id="p1",
            field="submit-btn",
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_submit_without_field(self) -> None:
        detector = MagicMock()
        validator = MagicMock()
        state = MagicMock()
        event_bus = MagicMock()
        event_bus.publish = AsyncMock()

        actions = FormActions(detector, validator, state, event_bus)
        page = MagicMock()
        form_locator = MagicMock()
        form_locator.click = AsyncMock()
        page.locator.return_value.first = form_locator

        result = await actions.submit(
            page=page,
            session_id="s1",
            browser_id="b1",
            context_id="c1",
            page_id="p1",
        )
        assert result["success"] is True


class TestFormActionsEvents:
    @pytest.mark.asyncio
    async def test_fill_publishes_form_started(self) -> None:
        detector = MagicMock()
        detector.detect = AsyncMock(
            return_value=[{"strategy": "css", "value": "#name"}]
        )
        validator = MagicMock()
        validator.validate = AsyncMock(
            return_value={
                "exists": True,
                "visible": True,
                "enabled": True,
                "editable": True,
                "checked": False,
            }
        )
        state = MagicMock()
        event_bus = MagicMock()
        event_bus.publish = AsyncMock()

        actions = FormActions(detector, validator, state, event_bus)
        page = MagicMock()
        page.locator.return_value.fill = AsyncMock()

        await actions.fill(
            page=page,
            session_id="s1",
            browser_id="b1",
            context_id="c1",
            page_id="p1",
            field="name",
            value="John",
        )
        event_names = [
            call[0][0].event_name for call in event_bus.publish.call_args_list
        ]
        assert "form.started" in event_names
        assert "form.field.filled" in event_names

    @pytest.mark.asyncio
    async def test_fill_failure_publishes_form_field_failed(self) -> None:
        detector = MagicMock()
        detector.detect = AsyncMock(side_effect=ValueError("not found"))
        validator = MagicMock()
        state = MagicMock()
        event_bus = MagicMock()
        event_bus.publish = AsyncMock()

        actions = FormActions(detector, validator, state, event_bus)
        page = MagicMock()

        result = await actions.fill(
            page=page,
            session_id="s1",
            browser_id="b1",
            context_id="c1",
            page_id="p1",
            field="bad",
            value="val",
        )
        assert result["success"] is False
        event_names = [
            call[0][0].event_name for call in event_bus.publish.call_args_list
        ]
        assert "form.started" in event_names
        assert "form.field.failed" in event_names

