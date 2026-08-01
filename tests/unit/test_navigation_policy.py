"""Tests for the navigation policy."""

from __future__ import annotations

import pytest

from browser_mcp.browser.navigation.policy import NavigationPolicy
from browser_mcp.config.models import BrowserSettings, NavigationStrategy
from browser_mcp.errors import PolicyViolationError

pytestmark = pytest.mark.unit


def make_policy(**overrides: object) -> NavigationPolicy:
    return NavigationPolicy(BrowserSettings(**overrides))


def test_allows_http_https_and_file() -> None:
    policy = make_policy()
    for url in ("https://example.com", "http://example.com", "file:///tmp/x.html"):
        assert policy.validate(url).allowed is True


def test_rejects_unknown_scheme() -> None:
    policy = make_policy()
    with pytest.raises(PolicyViolationError):
        policy.validate("javascript:alert(1)")


def test_rejects_scheme_when_restricted() -> None:
    policy = make_policy(navigation={"allowed_schemes": ["https"]})
    with pytest.raises(PolicyViolationError):
        policy.validate("http://example.com")


def test_rejects_url_without_scheme() -> None:
    policy = make_policy()
    with pytest.raises(PolicyViolationError):
        policy.validate("example.com/page")


def test_rejects_empty_url() -> None:
    policy = make_policy()
    with pytest.raises(PolicyViolationError):
        policy.validate("")


def test_blocks_exact_domain() -> None:
    policy = make_policy(navigation={"blocked_domains": ["example.com"]})
    with pytest.raises(PolicyViolationError):
        policy.validate("https://example.com/x")


def test_blocks_subdomain_of_blocked_domain() -> None:
    policy = make_policy(navigation={"blocked_domains": ["example.com"]})
    with pytest.raises(PolicyViolationError):
        policy.validate("https://ads.example.com/x")


def test_blocked_domain_case_insensitive() -> None:
    policy = make_policy(navigation={"blocked_domains": ["EXAMPLE.com"]})
    with pytest.raises(PolicyViolationError):
        policy.validate("https://example.com/x")


def test_allowed_domains_restrict_others() -> None:
    policy = make_policy(navigation={"allowed_domains": ["allowed.example"]})
    with pytest.raises(PolicyViolationError):
        policy.validate("https://other.example/x")
    assert policy.validate("https://allowed.example/x").allowed is True


def test_allowed_domains_permit_subdomains() -> None:
    policy = make_policy(navigation={"allowed_domains": ["allowed.example"]})
    assert policy.validate("https://sub.allowed.example/x").allowed is True


def test_empty_allowed_domains_allows_all() -> None:
    policy = make_policy(navigation={"allowed_domains": []})
    assert policy.validate("https://anything.example/x").allowed is True


def test_allowed_ports_reject_others() -> None:
    policy = make_policy(navigation={"allowed_ports": [8080]})
    with pytest.raises(PolicyViolationError):
        policy.validate("https://example.com:9090/x")
    assert policy.validate("https://example.com:8080/x").allowed is True


def test_blocked_extensions_reject() -> None:
    policy = make_policy(navigation={"blocked_extensions": [".exe"]})
    with pytest.raises(PolicyViolationError):
        policy.validate("https://example.com/install.exe")


def test_enforce_redirects_when_disabled() -> None:
    policy = make_policy(navigation={"allow_redirects": False})
    with pytest.raises(PolicyViolationError):
        policy.enforce_redirects(1)
    policy.enforce_redirects(0)


def test_enforce_redirects_max() -> None:
    policy = make_policy(navigation={"max_redirects": 3})
    policy.enforce_redirects(3)
    with pytest.raises(PolicyViolationError):
        policy.enforce_redirects(4)


def test_resolve_strategy_default() -> None:
    policy = make_policy()
    assert policy.resolve_strategy(None) is NavigationStrategy.NORMAL


def test_resolve_strategy_override() -> None:
    policy = make_policy()
    assert policy.resolve_strategy("fast") is NavigationStrategy.FAST


def test_resolve_strategy_invalid() -> None:
    policy = make_policy()
    with pytest.raises(PolicyViolationError):
        policy.resolve_strategy("turbo")
