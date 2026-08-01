"""Profile resolution and materialization.

Profiles control how browser state is isolated and whether it persists:

- ``temporary``: a fresh, disposable context (default).
- ``incognito``: a context created with privacy hardening.
- ``persistent``: a context backed by a stable on-disk user data directory.

Persistent profiles store their user data directories under the configured
profile root so a later session can resume the same browsing state.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from browser_mcp.config.models import BrowserProfile, BrowserSettings
from browser_mcp.errors import ProfileError

__all__ = ["ProfileManager", "ProfileSpec"]

_VALID_NAME = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


@dataclass(slots=True, frozen=True)
class ProfileSpec:
    """A resolved profile definition."""

    name: BrowserProfile
    label: str | None = None
    user_data_dir: Path | None = None

    @property
    def is_persistent(self) -> bool:
        """Return whether this profile persists on disk."""
        return self.name == BrowserProfile.PERSISTENT


class ProfileManager:
    """Resolves and materializes browser profiles."""

    def __init__(self, settings: BrowserSettings) -> None:
        self._settings = settings
        self._root = Path(settings.profiles.directory).expanduser()

    @property
    def root(self) -> Path:
        """Return the persistent profile root directory."""
        return self._root

    def resolve(self, profile: BrowserProfile | str, *, label: str | None = None) -> ProfileSpec:
        """Resolve ``profile`` into a concrete :class:`ProfileSpec`.

        Parameters
        ----------
        profile:
            One of ``temporary``, ``persistent``, or ``incognito``.
        label:
            Optional stable name for a persistent profile. Only alphanumeric,
            underscore, and hyphen characters are allowed.
        """
        try:
            resolved = BrowserProfile(profile)
        except ValueError as exc:
            raise ProfileError(f"unsupported profile '{profile}'") from exc

        if resolved is not BrowserProfile.PERSISTENT:
            return ProfileSpec(name=resolved, label=label)

        directory = self._materialize_persistent_dir(label)
        return ProfileSpec(name=resolved, label=label, user_data_dir=directory)

    def _materialize_persistent_dir(self, label: str | None) -> Path:
        if label is not None and not _VALID_NAME.match(label):
            raise ProfileError(
                f"persistent profile label '{label}' is invalid; "
                "use letters, digits, '_' or '-' only"
            )
        directory = self._root / label if label else self._root
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ProfileError(
                f"cannot create persistent profile directory '{directory}': {exc}"
            ) from exc
        return directory
