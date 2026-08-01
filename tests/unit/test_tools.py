"""Tests for the tool registry, decorators, and validation."""

from __future__ import annotations

import pytest

from enterprise_mcp.tools.decorators import get_tool_metadata, tool
from enterprise_mcp.tools.metadata import ToolMetadata
from enterprise_mcp.tools.registry import ToolRegistry
from enterprise_mcp.tools.validator import validate_input
from enterprise_mcp.utils.errors import ToolError

pytestmark = pytest.mark.unit


@tool(description="Add two integers.")
def add(a: int, b: int) -> int:
    """Sum two integers."""
    return a + b


@tool
async def greet(name: str = "world") -> str:
    """Greet someone."""
    return f"hello {name}"


async def test_decorator_attaches_metadata() -> None:
    metadata = get_tool_metadata(add)
    assert metadata is not None
    assert metadata.name == "add"
    assert metadata.description == "Add two integers."
    assert [p.name for p in metadata.parameters] == ["a", "b"]
    assert metadata.parameters[0].required


async def test_metadata_from_docstring_when_description_missing() -> None:
    metadata = get_tool_metadata(greet)
    assert metadata is not None
    assert "Greet someone." in metadata.description
    assert metadata.parameters[0].required is False


async def test_register_and_list() -> None:
    registry = ToolRegistry()
    registry.register(add)
    registry.register(greet)
    assert "add" in registry
    assert {m.name for m in registry.list()} == {"add", "greet"}


async def test_duplicate_registration_raises() -> None:
    registry = ToolRegistry()
    registry.register(add)
    with pytest.raises(ToolError):
        registry.register(add)


async def test_registration_requires_metadata() -> None:
    registry = ToolRegistry()

    def plain() -> None: ...

    with pytest.raises(ToolError):
        registry.register(plain)


async def test_call_sync_tool() -> None:
    registry = ToolRegistry()
    registry.register(add)
    assert await registry.call("add", a=2, b=3) == 5


async def test_call_async_tool() -> None:
    registry = ToolRegistry()
    registry.register(greet)
    assert await registry.call("greet", name="Ada") == "hello Ada"


async def test_call_unknown_tool_raises() -> None:
    registry = ToolRegistry()
    with pytest.raises(ToolError):
        await registry.call("missing")


async def test_validate_input_missing_required() -> None:
    metadata = ToolMetadata(name="add", parameters=[])
    validate_input(metadata, {})  # no parameters declared: nothing required
    from enterprise_mcp.tools.decorators import get_tool_metadata

    meta = get_tool_metadata(add)
    assert meta is not None
    with pytest.raises(ToolError):
        validate_input(meta, {"a": 1})


async def test_validate_input_unknown_parameter() -> None:
    meta = get_tool_metadata(add)
    assert meta is not None
    with pytest.raises(ToolError):
        validate_input(meta, {"a": 1, "b": 2, "c": 3})
