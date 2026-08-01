from __future__ import annotations

from browser_mcp.plugins.errors import CircularDependencyError, PluginDependencyError


class DependencyResolver:
    def resolve(self, manifests: dict[str, object]) -> list[str]:
        result: list[str] = []
        visiting: set[str] = set()
        visited: set[str] = set()
        def visit(name: str) -> None:
            if name in visited: return
            if name in visiting: raise CircularDependencyError(f"circular dependency involving '{name}'")
            manifest = manifests.get(name)
            if manifest is None: raise PluginDependencyError(f"plugin dependency '{name}' is not installed")
            visiting.add(name)
            for spec in getattr(manifest, "dependencies", []):
                visit(str(spec).split()[0])
            visiting.remove(name); visited.add(name); result.append(name)
        for name in manifests: visit(name)
        return result
