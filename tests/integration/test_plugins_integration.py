"""Integration tests for the plugin framework and form automation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from browser_mcp.plugins.base import Plugin
from browser_mcp.plugins.context import PluginContext
from browser_mcp.plugins.loader import PluginLoader
from browser_mcp.plugins.manifest import parse_manifest
from browser_mcp.plugins.registry import PluginRegistry


class TestPluginLifecycle:
    @pytest.mark.asyncio
    async def test_plugin_initialize_and_shutdown(self) -> None:
        plugin = MagicMock(spec=Plugin)
        plugin.initialize = AsyncMock()
        plugin.shutdown = AsyncMock()
        plugin.health = AsyncMock(return_value={"healthy": True})

        context = MagicMock()
        await plugin.initialize(context)
        plugin.initialize.assert_awaited_once_with(context)

        await plugin.shutdown()
        plugin.shutdown.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_plugin_registry_initialize_all(self) -> None:
        registry = PluginRegistry()
        plugin = MagicMock(spec=Plugin)
        plugin.initialize = AsyncMock()
        registry.register("test", plugin)

        context = MagicMock()
        await registry.initialize_all(context)
        plugin.initialize.assert_awaited_once_with(context)

    @pytest.mark.asyncio
    async def test_plugin_registry_shutdown_all(self) -> None:
        registry = PluginRegistry()
        plugin = MagicMock(spec=Plugin)
        plugin.shutdown = AsyncMock()
        registry.register("test", plugin)

        await registry.shutdown_all()
        plugin.shutdown.assert_awaited_once()


class TestPluginLoaderIntegration:
    def test_loader_with_manifest_dir(self, tmp_path: Path) -> None:
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()
        form_dir = plugins_dir / "forms"
        form_dir.mkdir()
        manifest_file = form_dir / "manifest.yaml"
        manifest_file.write_text(
            "name: browser.form\n"
            "version: 0.1.0\n"
            "entrypoint: browser_mcp.plugins.forms.tools:FormToolkit\n"
        )

        loader = PluginLoader(tmp_path)
        manifests = loader.discover()
        assert len(manifests) == 1
        assert manifests[0].name == "browser.form"

    def test_loader_discovers_multiple_manifests(self, tmp_path: Path) -> None:
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()

        for name in ["forms", "scraper"]:
            dir_path = plugins_dir / name
            dir_path.mkdir()
            manifest_file = dir_path / "manifest.yaml"
            manifest_file.write_text(
                f"name: browser.{name}\n"
                "version: 0.1.0\n"
                "entrypoint: browser_mcp.plugins.dummy:DummyPlugin\n"
            )

        loader = PluginLoader(tmp_path)
        manifests = loader.discover()
        assert len(manifests) == 2
        names = {m.name for m in manifests}
        assert "browser.forms" in names
        assert "browser.scraper" in names


class TestFormManifest:
    def test_forms_manifest_exists(self) -> None:
        manifest_path = (
            Path(__file__).parent.parent.parent
            / "src"
            / "browser_mcp"
            / "plugins"
            / "forms"
            / "manifest.yaml"
        )
        assert manifest_path.exists()

    def test_forms_manifest_parseable(self) -> None:
        manifest_path = (
            Path(__file__).parent.parent.parent
            / "src"
            / "browser_mcp"
            / "plugins"
            / "forms"
            / "manifest.yaml"
        )
        manifest = parse_manifest(manifest_path)
        assert manifest.name == "browser.form"
        assert manifest.category == "automation"
        assert "browser.page" in manifest.permissions
        assert "browser.element" in manifest.permissions


class TestFormToolkitRegistration:
    @pytest.mark.asyncio
    async def test_form_toolkit_registers_tools(self) -> None:
        from browser_mcp.plugins.forms.tools import FormToolkit

        actions = MagicMock()
        toolkit = FormToolkit(actions)

        registry = MagicMock()
        registry.register = MagicMock()
        toolkit.register(registry)

        assert registry.register.call_count == 5


class TestFormActionsWithMockPage:
    @pytest.mark.asyncio
    async def test_fill_calls_page_locator_fill(self) -> None:
        from browser_mcp.plugins.forms.actions import FormActions

        detector = MagicMock()
        detector.detect = AsyncMock(return_value=[{"strategy": "css", "value": "#email"}])
        validator = MagicMock()
        validator.validate = AsyncMock(return_value={"exists": True, "visible": True, "enabled": True, "editable": True, "checked": False})
        state = MagicMock()
        event_bus = MagicMock()
        event_bus.publish = AsyncMock()

        actions = FormActions(detector, validator, state, event_bus)
        page = MagicMock()
        locator = MagicMock()
        page.locator.return_value = locator
        locator.fill = AsyncMock()

        result = await actions.fill(
            page=page,
            session_id="s1",
            browser_id="b1",
            context_id="c1",
            page_id="p1",
            field="email",
            value="user@example.com",
        )
        assert result["success"] is True
        page.locator.assert_called()
        locator.fill.assert_awaited_once_with("user@example.com")

    @pytest.mark.asyncio
    async def test_submit_clicks_form(self) -> None:
        from browser_mcp.plugins.forms.actions import FormActions

        detector = MagicMock()
        validator = MagicMock()
        state = MagicMock()
        event_bus = MagicMock()
        event_bus.publish = AsyncMock()

        actions = FormActions(detector, validator, state, event_bus)
        page = MagicMock()
        form_locator = MagicMock()
        form_locator.first = MagicMock()
        form_locator.first.click = AsyncMock()
        page.locator.return_value = form_locator

        result = await actions.submit(
            page=page,
            session_id="s1",
            browser_id="b1",
            context_id="c1",
            page_id="p1",
        )
        assert result["success"] is True


class TestFormPluginContext:
    def test_plugin_context_exposes_services(self) -> None:
        app_context = MagicMock()
        container = MagicMock()
        browser_manager = MagicMock()
        browser_pool = MagicMock()
        session_manager = MagicMock()
        element_engine = MagicMock()
        state_manager = MagicMock()
        event_bus = MagicMock()

        context = PluginContext(
            app_context=app_context,
            container=container,
            browser_manager=browser_manager,
            browser_pool=browser_pool,
            session_manager=session_manager,
            element_engine=element_engine,
            state_manager=state_manager,
            event_bus=event_bus,
        )

        assert context.app_context is app_context
        assert context.container is container
        assert context.browser_manager is browser_manager
        assert context.browser_pool is browser_pool
        assert context.session_manager is session_manager
        assert context.element_engine is element_engine
        assert context.state_manager is state_manager
        assert context.event_bus is event_bus

    def test_plugin_context_settings(self, tmp_path: Path) -> None:
        settings = MagicMock()
        app_context = MagicMock()
        app_context.settings = settings

        context = PluginContext(
            app_context=app_context,
            container=MagicMock(),
            browser_manager=MagicMock(),
            browser_pool=MagicMock(),
            session_manager=MagicMock(),
            element_engine=MagicMock(),
            state_manager=MagicMock(),
            event_bus=MagicMock(),
        )
        assert context.settings is settings
