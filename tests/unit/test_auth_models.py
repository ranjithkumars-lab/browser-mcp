"""Tests for the authentication domain models."""

from __future__ import annotations

import pytest

from browser_mcp.auth.models import (
    AuthCredentials,
    AuthHeaders,
    AuthMetadata,
    AuthSession,
    AuthState,
    CookieCollection,
)

pytestmark = pytest.mark.unit


class TestAuthCredentials:
    def test_defaults(self) -> None:
        creds = AuthCredentials(username="user", password="pass", url="https://example.com/login")
        assert creds.strategy == "form"
        assert creds.headers == {}
        assert creds.cookies == {}
        assert creds.metadata == {}

    def test_full(self) -> None:
        creds = AuthCredentials(
            username="u",
            password="p",
            url="https://example.com",
            strategy="header",
            headers={"X-API-Key": "secret"},
            cookies={"session": "abc"},
            metadata={"extra": 1},
        )
        assert creds.headers == {"X-API-Key": "secret"}
        assert creds.metadata == {"extra": 1}


class TestAuthHeaders:
    def test_defaults(self) -> None:
        h = AuthHeaders()
        assert h.strategy == "header"
        assert h.headers == {}

    def test_with_headers(self) -> None:
        h = AuthHeaders(headers={"Authorization": "Bearer token"})
        assert h.headers["Authorization"] == "Bearer token"


class TestCookieCollection:
    def test_defaults(self) -> None:
        c = CookieCollection()
        assert c.strategy == "cookie"
        assert c.cookies == []


class TestAuthMetadata:
    def test_defaults(self) -> None:
        m = AuthMetadata(strategy="form", context_id="ctx-1", session_id="ses-1")
        assert m.strategy == "form"
        assert m.context_id == "ctx-1"
        assert m.session_id == "ses-1"
        assert m.last_refreshed_at is None
        assert m.expires_at is None


class TestAuthSession:
    def test_defaults(self) -> None:
        s = AuthSession(session_id="ses-1", context_id="ctx-1")
        assert s.authenticated is False
        assert s.metadata is None

    def test_with_metadata(self) -> None:
        m = AuthMetadata(strategy="form", context_id="ctx-1", session_id="ses-1")
        s = AuthSession(session_id="ses-1", context_id="ctx-1", authenticated=True, metadata=m)
        assert s.authenticated is True
        assert s.metadata.strategy == "form"


class TestAuthState:
    def test_defaults(self) -> None:
        session = AuthSession(session_id="ses-1", context_id="ctx-1")
        state = AuthState(session=session)
        assert state.session.session_id == "ses-1"
        assert state.state_id
        assert state.created_at <= state.updated_at

    def test_serialization(self) -> None:
        session = AuthSession(session_id="ses-1", context_id="ctx-1")
        state = AuthState(session=session)
        data = state.model_dump(mode="json")
        assert data["session"]["session_id"] == "ses-1"
        assert "state_id" in data
