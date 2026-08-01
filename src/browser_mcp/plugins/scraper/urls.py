"""URL normalisation utilities for the scraper plugin.

Provides deterministic, scheme-filtered absolute-URL resolution used by the
``links`` and ``images`` collectors. Relative URLs are resolved against a
``base_url``; unsupported schemes (``mailto:``, ``tel:``, ``javascript:``,
``data:``, ...) are rejected.
"""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

__all__ = [
    "BLOCKED_SCHEMES",
    "is_anchor_link",
    "is_internal",
    "normalize_href",
]

BLOCKED_SCHEMES = frozenset({"mailto", "tel", "javascript", "data", "ftp", "blob", "file"})


def normalize_href(raw_href: str, base_url: str | None) -> str | None:
    """Resolve ``raw_href`` to an absolute URL against ``base_url``.

    Returns ``None`` when the href is empty, the scheme is unsupported, or
    the value cannot be parsed.

    Resolution pipeline (single source of truth):
    raw href -> strip -> reject pure fragments -> reject blocked schemes ->
    resolve relative/protocol-relative via ``urljoin`` -> reject blocked after
    resolution -> strip trailing slash.
    """
    if not raw_href or not raw_href.strip():
        return None

    stripped = raw_href.strip()

    # Pure fragment navigation is handled by ``is_anchor_link``; ``None``
    # signals "not an absolute resource URL".
    if stripped.startswith("#"):
        return None

    parsed = urlparse(stripped)
    if parsed.scheme.lower() in BLOCKED_SCHEMES:
        return None

    # No scheme => relative path or protocol-relative URL (``//host/path``).
    # ``urljoin`` handles both forms, inheriting the scheme from ``base_url``.
    if not parsed.scheme:
        if not base_url:
            return None
        joined = urljoin(base_url, stripped)
        resolved = urlparse(joined)
        if resolved.scheme.lower() in BLOCKED_SCHEMES:
            return None
        return joined.rstrip("/")

    return stripped.rstrip("/")


def is_internal(resolved_url: str, base_url: str | None) -> bool | None:
    """Return whether ``resolved_url`` shares the host of ``base_url``.

    Returns ``None`` when ``base_url`` has no resolvable host (e.g.
    ``about:blank`` or an empty string), so callers can fall back to
    heuristic classification instead of misclassifying.
    """
    if not base_url:
        return None
    base_host = urlparse(base_url).hostname
    target_host = urlparse(resolved_url).hostname
    if not base_host or not target_host:
        return None
    return base_host == target_host


def is_anchor_link(resolved_url: str, base_url: str | None) -> bool | None:
    """Return True when ``resolved_url`` is same-page fragment navigation."""
    if not resolved_url:
        return None
    if base_url:
        base_norm = base_url.rstrip("/")
        if "#" in resolved_url:
            path_part, fragment = resolved_url.split("#", 1)
            path_norm = path_part.rstrip("/")
            normalized = f"{path_norm}#{fragment}"
        else:
            normalized = resolved_url.rstrip("/")
        return normalized.startswith(base_norm + "#")
    return resolved_url.startswith("#")
