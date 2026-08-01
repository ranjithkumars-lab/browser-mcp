"""Typed Browser Events Engine schemas."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import IntEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class EventPriority(IntEnum):
    LOW = 10
    NORMAL = 20
    HIGH = 30
    CRITICAL = 40


class EventHeader(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_{uuid4().hex}")
    correlation_id: str | None = None
    parent_event_id: str | None = None
    trace_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    priority: EventPriority = EventPriority.NORMAL


class NavigationPayload(BaseModel):
    url: str | None = None
    previous_url: str | None = None
    action: str | None = None


class TransferPayload(BaseModel):
    transfer_id: str | None = None
    progress_percentage: float | None = Field(default=None, ge=0, le=100)
    bytes_received: int | None = Field(default=None, ge=0)
    speed_bps: float | None = Field(default=None, ge=0)


class AuthenticationPayload(BaseModel):
    strategy: str | None = None
    authenticated: bool | None = None


class PluginPayload(BaseModel):
    plugin_name: str | None = None
    action: str | None = None


class ElementPayload(BaseModel):
    element_id: str | None = None
    selector: str | None = None
    action: str | None = None


class BrowserEvent(BaseModel):
    header: EventHeader = Field(default_factory=EventHeader)
    event_type: str = Field(min_length=1)
    category: str = Field(min_length=1)
    meta: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)

    @property
    def event_id(self) -> str: return self.header.event_id
    @property
    def priority(self) -> EventPriority: return self.header.priority
