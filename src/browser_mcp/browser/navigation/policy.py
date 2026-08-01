"""Enterprise navigation boundaries.

:class:`NavigationPolicy` enforces navigation policy before a page is told to
navigate, and validates redirect behavior after navigation completes.

Implemented rules:

- ``allowed_domains`` / ``blocked_domains``
- ``allowed_schemes``
- ``blocked_extensions`` (path suffix check)
- ``allowed_ports``
- ``allow_redirects`` / ``max_redirects`` (enforced from the redirect chain)

Reserved (parsed, validated, but not yet enforced):

- ``max_navigation_depth``

Redirects are detected from the navigation response after the fact; Playwright
follows HTTP redirects at the network level, so we reject a navigation whose
redirect chain violates the configured policy rather than attempting to
intercept and rewrite requests (which is deferred to a future route layer).
"""

from __future__ import annotations

from urllib.parse import urlsplit

from browser_mcp.config.models import BrowserSettings, NavigationConfig, NavigationStrategy
from browser_mcp.errors import PolicyViolationError

__all__ = ["NavigationPolicy", "PolicyResult"]


class PolicyResult:
    """Outcome of a navigation policy check."""

    __slots__ = ("allowed", "normalized_url", "reason")

    def __init__(
        self, *, allowed: bool, reason: str | None = None, normalized_url: str = ""
    ) -> None:
        self.allowed = allowed
        self.reason = reason
        self.normalized_url = normalized_url


def _normalize_host(host: str | None) -> str:
    if not host:
        return ""
    return host.strip().lower().rstrip(".")


def _host_matches(host: str, rule: str) -> bool:
    """Return whether ``host`` is ``rule`` or a subdomain of it."""
    return host == rule or host.endswith(f".{rule}")


class NavigationPolicy:
    """Validates navigation requests against configured boundaries."""

    def __init__(self, settings: BrowserSettings) -> None:
        self._settings = settings

    @property
    def config(self) -> NavigationConfig:
        """Return the resolved navigation configuration."""
        return self._settings.navigation

    def validate(self, url: str) -> PolicyResult:
        """Validate ``url`` against the navigation policy.

        Raises
        ------
        PolicyViolationError
            When the URL is not navigable under the configured policy.
        """
        if not url:
            raise PolicyViolationError("navigation url must not be empty")

        parts = urlsplit(url)
        scheme = (parts.scheme or "").lower()
        host = _normalize_host(parts.hostname)
        port = parts.port
        path = parts.path or "/"

        config = self.config
        if scheme and config.allowed_schemes and scheme not in config.allowed_schemes:
            raise PolicyViolationError(
                f"scheme '{scheme}' is not allowed; allowed schemes: "
                f"{', '.join(sorted(config.allowed_schemes))}"
            )
        if not scheme:
            raise PolicyViolationError("navigation url has no scheme")

        if host:
            for blocked in config.blocked_domains:
                if _host_matches(host, _normalize_host(blocked)):
                    raise PolicyViolationError(f"domain '{host}' is blocked by navigation policy")
            if config.allowed_domains and not any(
                _host_matches(host, _normalize_host(rule)) for rule in config.allowed_domains
            ):
                raise PolicyViolationError(
                    f"domain '{host}' is not in the allowed domains: "
                    f"{', '.join(sorted(config.allowed_domains))}"
                )

        if config.allowed_ports and port is not None and port not in config.allowed_ports:
            raise PolicyViolationError(
                f"port '{port}' is not in the allowed ports: {sorted(config.allowed_ports)}"
            )

        if config.blocked_extensions and any(
            path.lower().endswith(extension.lower()) for extension in config.blocked_extensions
        ):
            raise PolicyViolationError(
                f"path '{path}' ends in a blocked extension: {config.blocked_extensions}"
            )

        return PolicyResult(allowed=True, normalized_url=url)

    def enforce_redirects(self, redirect_count: int) -> None:
        """Reject a navigation whose redirect chain violates policy.

        Parameters
        ----------
        redirect_count:
            Number of redirect hops observed for the navigation.
        """
        config = self.config
        if not config.allow_redirects and redirect_count > 0:
            raise PolicyViolationError(
                f"navigation followed {redirect_count} redirect(s) but "
                "redirects are disabled by policy"
            )
        if redirect_count > config.max_redirects:
            raise PolicyViolationError(
                f"navigation exceeded max_redirects={config.max_redirects} "
                f"({redirect_count} redirects)"
            )

    def resolve_strategy(self, strategy: NavigationStrategy | str | None) -> NavigationStrategy:
        """Resolve ``strategy`` or fall back to the configured default."""
        if strategy is None:
            return self.config.default_strategy
        try:
            return NavigationStrategy(strategy)
        except ValueError as exc:
            raise PolicyViolationError(f"unsupported navigation_strategy '{strategy}'") from exc
