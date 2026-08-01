"""Tests for the Phase 2 error hierarchy."""

from __future__ import annotations

import pytest

from browser_mcp.errors import (
    BrowserError,
    DownloadError,
    FrameError,
    InteractionError,
    NavigationError,
    NavigationTimeoutError,
    PolicyViolationError,
    PopupError,
)

pytestmark = pytest.mark.unit


def test_navigation_subclasses_browser_error() -> None:
    assert issubclass(NavigationError, BrowserError)


def test_timeout_error_hierarchy() -> None:
    assert issubclass(NavigationTimeoutError, NavigationError)
    assert issubclass(NavigationTimeoutError, BrowserError)
    assert not issubclass(NavigationTimeoutError, TimeoutError)


def test_frame_error_hierarchy() -> None:
    assert issubclass(FrameError, NavigationError)


def test_popup_error_hierarchy() -> None:
    assert issubclass(PopupError, NavigationError)


def test_interaction_error_hierarchy() -> None:
    assert issubclass(InteractionError, NavigationError)


def test_policy_violation_hierarchy() -> None:
    assert issubclass(PolicyViolationError, NavigationError)


def test_download_error_hierarchy() -> None:
    assert issubclass(DownloadError, NavigationError)


def test_specific_errors_are_catchable_as_navigation() -> None:
    for exc_type in (
        NavigationTimeoutError,
        FrameError,
        PopupError,
        InteractionError,
        PolicyViolationError,
        DownloadError,
    ):
        try:
            raise exc_type("boom")
        except NavigationError as exc:
            assert isinstance(exc, exc_type)
