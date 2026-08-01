"""Tests for the plugin framework."""

from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml

from browser_mcp.plugins.base import Plugin
from browser_mcp.plugins.loader import PluginLoader, _split_entrypoint
from browser_mcp.plugins.manifest import PluginManifest, parse_manifest
from browser_mcp.plugins.permissions import Permissions
from browser_mcp.plugins.registry import PluginRegistry


class TestPluginManifest:
    def test_from_dict(self) -> None:
        data = {
            "name": "test.plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "permissions": ["browser.page"],
            "category": "automation",
            "tools": ["browser.test.action"],
            "entrypoint": "test.module:TestPlugin",
        }
        manifest = PluginManifest.from_dict(data)
        assert manifest.name == "test.plugin"
        assert manifest.version == "1.0.0"
        assert manifest.description == "A test plugin"
        assert manifest.permissions == ["browser.page"]
        assert manifest.category == "automation"
        assert manifest.tools == ["browser.test.action"]
        assert manifest.entrypoint == "test.module:TestPlugin"

    def test_to_dict(self) -> None:
        manifest = PluginManifest(
            name="test.plugin",
            version="1.0.0",
            description="A test plugin",
            permissions=["browser.page"],
            category="automation",
            tools=["browser.test.action"],
            entrypoint="test.module:TestPlugin",
        )
        d = manifest.to_dict()
        assert d["name"] == "test.plugin"
        assert d["entrypoint"] == "test.module:TestPlugin"

    def test_parse_manifest_yaml(self, tmp_path: Path) -> None:
        manifest_file = tmp_path / "manifest.yaml"
        manifest_file.write_text(
            yaml.dump(
                {
                    "name": "yaml.plugin",
                    "entrypoint": "mod:Cls",
                }
            )
        )
        result = parse_manifest(manifest_file)
        assert result.name == "yaml.plugin"
        assert result.entrypoint == "mod:Cls"

    def test_parse_manifest_json(self, tmp_path: Path) -> None:
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text(json.dumps({"name": "json.plugin", "entrypoint": "mod:Cls"}))
        result = parse_manifest(manifest_file)
        assert result.name == "json.plugin"
        assert result.entrypoint == "mod:Cls"

    def test_parse_manifest_missing_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            parse_manifest(Path("/nonexistent/manifest.yaml"))

    def test_parse_manifest_missing_entrypoint(self, tmp_path: Path) -> None:
        manifest_file = tmp_path / "manifest.yaml"
        manifest_file.write_text(yaml.dump({"name": "bad.plugin"}))
        with pytest.raises(ValueError, match="entrypoint"):
            parse_manifest(manifest_file)

    def test_parse_manifest_unsupported_format(self, tmp_path: Path) -> None:
        manifest_file = tmp_path / "manifest.txt"
        manifest_file.write_text("name: bad")
        with pytest.raises(ValueError, match="Unsupported"):
            parse_manifest(manifest_file)


class TestPluginRegistry:
    def test_register_and_get(self) -> None:
        registry = PluginRegistry()
        plugin = MagicMock(spec=Plugin)
        registry.register("test", plugin)
        assert registry.get("test") is plugin

    def test_register_duplicate_raises(self) -> None:
        registry = PluginRegistry()
        plugin = MagicMock(spec=Plugin)
        registry.register("test", plugin)
        with pytest.raises(ValueError, match="already registered"):
            registry.register("test", plugin)

    def test_remove(self) -> None:
        registry = PluginRegistry()
        plugin = MagicMock(spec=Plugin)
        registry.register("test", plugin)
        removed = registry.remove("test")
        assert removed is plugin
        assert registry.remove("test") is None

    def test_names(self) -> None:
        registry = PluginRegistry()
        registry.register("a", MagicMock(spec=Plugin))
        registry.register("b", MagicMock(spec=Plugin))
        assert set(registry.names()) == {"a", "b"}

    def test_len(self) -> None:
        registry = PluginRegistry()
        assert len(registry) == 0
        registry.register("a", MagicMock(spec=Plugin))
        assert len(registry) == 1

    def test_health_all(self) -> None:
        registry = PluginRegistry()
        plugin = MagicMock(spec=Plugin)
        plugin.health = AsyncMock(return_value={"healthy": True})
        registry.register("ok", plugin)
        registry.register("fail", MagicMock(spec=Plugin))
        registry.get("fail").health = AsyncMock(side_effect=RuntimeError("boom"))

        import asyncio

        results = asyncio.run(registry.health_all())
        assert results["ok"] == {"healthy": True}
        assert results["fail"]["healthy"] is False


class TestSplitEntrypoint:
    def test_valid_entrypoint(self) -> None:
        module, cls = _split_entrypoint("my.module:MyClass")
        assert module == "my.module"
        assert cls == "MyClass"

    def test_missing_colon(self) -> None:
        with pytest.raises(
            ValueError,
            match=re.escape("module.path:ClassName"),
        ):
            _split_entrypoint("invalid")


class TestPluginLoader:
    def test_discover_empty_dir(self, tmp_path: Path) -> None:
        loader = PluginLoader(tmp_path)
        manifests = loader.discover()
        assert manifests == []

    def test_discover_no_manifests(self, tmp_path: Path) -> None:
        (tmp_path / "other.txt").write_text("not a manifest")
        loader = PluginLoader(tmp_path)
        manifests = loader.discover()
        assert manifests == []

    def test_discover_yaml_manifest(self, tmp_path: Path) -> None:
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()
        manifest_file = plugins_dir / "manifest.yaml"
        manifest_file.write_text("name: test.plugin\nentrypoint: test.module:TestPlugin\n")
        loader = PluginLoader(tmp_path)
        manifests = loader.discover()
        assert len(manifests) == 1
        assert manifests[0].name == "test.plugin"

    def test_load_nonexistent_entrypoint(self) -> None:
        registry = PluginRegistry()
        loader = PluginLoader(Path("tests/fixtures/nonexistent"), registry)
        with pytest.raises(ModuleNotFoundError):
            loader.load(
                PluginManifest(
                    name="bad",
                    version="0.1.0",
                    description="",
                    permissions=[],
                    category="test",
                    tools=[],
                    entrypoint="nonexistent.module:NonexistentClass",
                )
            )


class TestPermissions:
    def test_grant_and_has(self) -> None:
        perms = Permissions()
        perms.grant("browser.page")
        assert perms.has("browser.page")

    def test_revoke(self) -> None:
        perms = Permissions(["browser.page", "browser.element"])
        perms.revoke("browser.page")
        assert not perms.has("browser.page")
        assert perms.has("browser.element")

    def test_all(self) -> None:
        perms = Permissions(["a", "b", "c"])
        assert perms.all() == frozenset({"a", "b", "c"})

    def test_empty(self) -> None:
        perms = Permissions()
        assert perms.all() == frozenset()
