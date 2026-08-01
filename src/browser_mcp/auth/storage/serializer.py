"""Serialise and deserialise Playwright storage_state JSON."""

from __future__ import annotations

import json
from typing import Any

__all__ = ["StateSerializer"]


class StateSerializer:
    """Serialize/deserialize Playwright ``storage_state`` JSON."""

    def serialize(self, state: dict[str, Any]) -> str:
        return json.dumps(state, default=str)

    def deserialize(self, payload: str) -> dict[str, Any]:
        return json.loads(payload)
