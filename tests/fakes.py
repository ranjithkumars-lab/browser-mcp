"""Fake Playwright objects for unit-testing the navigation and element engines.

The fakes mirror just enough of ``playwright.async_api`` to exercise the real
navigation managers without launching a browser. Each fake page/frame carries a
unique ``_impl_obj.guid`` so the identity-based frame and popup tracking in the
real managers behaves as it would against Playwright.

Element support mirrors ``Locator``: every fake locator wraps a list of
:class:`FakeElement` values, so the element engine's queries (count, text,
HTML, attributes, state) are fully unit-testable.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from uuid import uuid4


def _new_guid() -> str:
    return uuid4().hex


class FakeElement:
    """Minimal DOM node backing :class:`FakeLocator` queries."""

    def __init__(
        self,
        *,
        text: str = "",
        tag: str = "div",
        attrs: dict[str, str] | None = None,
        visible: bool = True,
        enabled: bool = True,
        editable: bool = False,
        checked: bool = False,
        disabled: bool = False,
    ) -> None:
        self.text = text
        self.tag = tag
        self.attrs = dict(attrs or {})
        self.visible = visible
        self.enabled = enabled
        self.editable = editable
        self.checked = checked
        self.disabled = disabled

    @property
    def html(self) -> str:
        return self.attrs.get("data-html") or f"<{self.tag}>{self.text}</{self.tag}>"

    @property
    def outer_html(self) -> str:
        return self.attrs.get("data-outer-html") or f"<{self.tag}>{self.text}</{self.tag}>"


class FakeLocator:
    """Minimal locator recording performed actions and supporting queries."""

    def __init__(
        self,
        selector: str,
        frame: FakeFrame | None = None,
        elements: list[FakeElement] | None = None,
    ) -> None:
        self.selector = selector
        self.frame = frame
        self.clicks = 0
        self.dblclicks = 0
        self.hovers = 0
        self.scrolled = 0
        self.fail_next = False
        self.elements = elements if elements is not None else [FakeElement()]
        self.wait_for_error: Exception | None = None
        self.last_wait_state: str | None = None
        self.evaluate_result: Any = None

    @property
    def element(self) -> FakeElement | None:
        return self.elements[0] if self.elements else None

    # -- actions --------------------------------------------------------

    async def click(self, **_: Any) -> None:
        if self.fail_next:
            raise RuntimeError("locator click failed")
        self.clicks += 1

    async def dblclick(self, **_: Any) -> None:
        if self.fail_next:
            raise RuntimeError("locator dblclick failed")
        self.dblclicks += 1

    async def hover(self, **_: Any) -> None:
        if self.fail_next:
            raise RuntimeError("locator hover failed")
        self.hovers += 1

    async def scroll_into_view_if_needed(self, **_: Any) -> None:
        if self.fail_next:
            raise RuntimeError("locator scroll failed")
        self.scrolled += 1

    async def evaluate(self, expression: str, arg: Any = None) -> Any:
        return self.evaluate_result

    # -- queries --------------------------------------------------------

    async def count(self) -> int:
        return len(self.elements)

    def nth(self, index: int) -> FakeLocator:
        element = self.elements[index] if index < len(self.elements) else None
        return FakeLocator(self.selector, frame=self.frame, elements=[element] if element else [])

    def first(self) -> FakeLocator:
        return self.nth(0)

    def _require(self) -> FakeElement:
        element = self.element
        if element is None:
            raise RuntimeError(f"no element matched '{self.selector}'")
        return element

    async def inner_text(self) -> str:
        return self._require().text

    async def text_content(self) -> str | None:
        return self._require().text

    async def inner_html(self) -> str:
        return self._require().html

    async def outer_html(self) -> str:
        return self._require().outer_html

    async def get_attribute(self, name: str) -> str | None:
        return self._require().attrs.get(name)

    async def is_visible(self) -> bool:
        element = self.element
        return element is not None and element.visible

    async def is_enabled(self) -> bool:
        element = self.element
        return element is not None and element.enabled

    async def is_editable(self) -> bool:
        element = self.element
        return element is not None and element.editable

    async def is_checked(self) -> bool:
        element = self.element
        return element is not None and element.checked

    async def is_disabled(self) -> bool:
        element = self.element
        return element is not None and element.disabled

    async def wait_for(self, state: str = "attached", timeout: int | None = None) -> None:
        self.last_wait_state = state
        if self.wait_for_error is not None:
            raise self.wait_for_error
        if self.element is None:
            raise RuntimeError(f"element did not reach state '{state}'")


class FakeLocatorProvider:
    """Stand-in for :class:`LocatorProvider` driving the fake locators.

    Mirrors :class:`PlaywrightLocatorProvider` exactly, but returns fakes and
    never touches the Playwright driver.
    """

    def create_css(self, target: Any, value: str) -> FakeLocator:
        return target.locator(value)

    def create_xpath(self, target: Any, value: str) -> FakeLocator:
        return target.locator(f"xpath={value}")

    def create_text(self, target: Any, value: str, *, exact: bool = False) -> FakeLocator:
        return target.get_by_text(value, exact=exact)

    def create_role(
        self,
        target: Any,
        role: str,
        *,
        name: str | None = None,
        exact: bool = False,
    ) -> FakeLocator:
        return target.get_by_role(role, name=name, exact=exact)

    def create_playwright(self, target: Any, value: str) -> FakeLocator:
        return target.locator(value)

    def nth(self, locator: FakeLocator, index: int) -> FakeLocator:
        return locator.nth(index)

    async def count(self, locator: FakeLocator) -> int:
        return await locator.count()

    async def inner_text(self, locator: FakeLocator) -> str:
        return await locator.inner_text()

    async def inner_html(self, locator: FakeLocator) -> str:
        return await locator.inner_html()

    async def outer_html(self, locator: FakeLocator) -> str:
        return await locator.outer_html()

    async def get_attribute(self, locator: FakeLocator, name: str) -> str | None:
        return await locator.get_attribute(name)

    async def is_visible(self, locator: FakeLocator) -> bool:
        return await locator.is_visible()

    async def is_enabled(self, locator: FakeLocator) -> bool:
        return await locator.is_enabled()

    async def is_editable(self, locator: FakeLocator) -> bool:
        return await locator.is_editable()

    async def is_checked(self, locator: FakeLocator) -> bool:
        return await locator.is_checked()

    async def is_disabled(self, locator: FakeLocator) -> bool:
        return await locator.is_disabled()

    async def wait_for(
        self,
        locator: FakeLocator,
        state: str = "attached",
        timeout: int | None = None,
        *,
        strict: bool | None = None,
    ) -> None:
        target = locator.first() if strict is False else locator
        await target.wait_for(state=state, timeout=timeout)


class FakeRequest:
    """Minimal request supporting a redirect chain."""

    def __init__(self, redirected_from: FakeRequest | None = None) -> None:
        self.redirected_from = redirected_from


class FakeResponse:
    """Minimal response with a status and redirect chain."""

    def __init__(self, status: int = 200, redirected_from: FakeRequest | None = None) -> None:
        self.status = status
        self.request = FakeRequest(redirected_from)


def redirect_chain(length: int, status: int = 200) -> FakeResponse:
    """Return a response whose request chain has ``length`` redirect hops."""
    previous: FakeRequest | None = None
    for _ in range(length):
        previous = FakeRequest(previous)
    return FakeResponse(status=status, redirected_from=previous)


class FakeFrame:
    """Minimal Playwright frame with a unique stable guid."""

    def __init__(
        self,
        guid: str | None = None,
        name: str = "",
        url: str = "about:blank",
        parent: FakeFrame | None = None,
    ) -> None:
        self._impl_obj = SimpleNamespace(_guid=guid or _new_guid())
        self._name = name
        self._url = url
        self._parent = parent
        self._elements_by_selector: dict[str, list[FakeElement]] = {}

    @property
    def name(self) -> str:
        return self._name

    @property
    def url(self) -> str:
        return self._url

    @property
    def parent_frame(self) -> FakeFrame | None:
        return self._parent

    def set_elements(self, selector: str, elements: list[FakeElement]) -> None:
        self._elements_by_selector[selector] = elements

    def locator(self, selector: str) -> FakeLocator:
        return FakeLocator(
            selector,
            frame=self,
            elements=list(self._elements_by_selector.get(selector, [FakeElement()])),
        )

    def get_by_text(self, text: str, exact: bool = False) -> FakeLocator:
        return self.locator(f"text={text}")

    def get_by_role(self, role: str, name: str | None = None, exact: bool = False) -> FakeLocator:
        key = f"role={role}" + (f":{name}" if name else "")
        return self.locator(key)

    async def evaluate(self, expression: str, arg: Any = None) -> Any:
        return None


class FakeContext:
    """Minimal browser context supporting the ``page`` event."""

    def __init__(self) -> None:
        self.pages: list[FakePage] = []
        self._page_listeners: list[Any] = []

    def on(self, event: str, handler: Any) -> None:
        if event == "page":
            self._page_listeners.append(handler)

    def remove_listener(self, event: str, handler: Any) -> None:
        if event == "page" and handler in self._page_listeners:
            self._page_listeners.remove(handler)

    def emit_page(self, page: FakePage) -> None:
        self.pages.append(page)
        for handler in list(self._page_listeners):
            handler(page)


class FakePage:
    """Minimal Playwright page with a unique stable impl guid."""

    def __init__(
        self,
        url: str = "about:blank",
        title: str = "",
        *,
        frames: list[FakeFrame] | None = None,
        context: FakeContext | None = None,
    ) -> None:
        self._impl_obj = SimpleNamespace(_guid=_new_guid())
        self._url = url
        self._title = title
        self._frames = frames or [FakeFrame(url=url)]
        self.context = context or FakeContext()
        self.context.pages.append(self)
        self._download_listeners: list[Any] = []
        self._locators: dict[str, FakeLocator] = {}
        self._elements_by_selector: dict[str, list[FakeElement]] = {}
        self.last_goto: tuple[str, dict[str, Any]] | None = None
        self.last_reload: dict[str, Any] | None = None
        self.last_wait_for_load_state: tuple[str, Any] | None = None
        self.last_wait_for_url: tuple[str, Any] | None = None
        self.navigations: list[str] = []
        self.evaluations: list[tuple[str, Any]] = []
        self.goto_response: FakeResponse | None = None
        self.goto_error: Exception | None = None
        self.reload_response: FakeResponse | None = None
        self.reload_error: Exception | None = None
        self.wait_for_url_error: Exception | None = None
        self.wait_for_load_state_error: Exception | None = None

    @property
    def url(self) -> str:
        return self._url

    @property
    def main_frame(self) -> FakeFrame:
        return self._frames[0]

    @property
    def frames(self) -> list[FakeFrame]:
        return list(self._frames)

    async def title(self) -> str:
        return self._title

    async def goto(self, url: str, **kwargs: Any) -> FakeResponse:
        self.last_goto = (url, kwargs)
        self.navigations.append(url)
        if self.goto_error is not None:
            raise self.goto_error
        if self.goto_response is not None:
            return self.goto_response
        self._url = url
        return FakeResponse(status=200)

    async def reload(self, **kwargs: Any) -> FakeResponse:
        self.last_reload = kwargs
        self.navigations.append("__reload__")
        if self.reload_error is not None:
            raise self.reload_error
        if self.reload_response is not None:
            return self.reload_response
        return FakeResponse(status=200)

    async def go_back(self, **kwargs: Any) -> FakeResponse:
        self.navigations.append("__back__")
        return FakeResponse(status=200)

    async def go_forward(self, **kwargs: Any) -> FakeResponse:
        self.navigations.append("__forward__")
        return FakeResponse(status=200)

    async def wait_for_load_state(self, state: str = "load", **kwargs: Any) -> None:
        self.last_wait_for_load_state = (state, kwargs.get("timeout"))
        if self.wait_for_load_state_error is not None:
            raise self.wait_for_load_state_error
        return None

    async def wait_for_url(self, pattern: str, **kwargs: Any) -> None:
        self.last_wait_for_url = (pattern, kwargs.get("timeout"))
        if self.wait_for_url_error is not None:
            raise self.wait_for_url_error
        return None

    async def evaluate(self, expression: str, arg: Any = None) -> Any:
        self.evaluations.append((expression, arg))
        return None

    async def bring_to_front(self) -> None:
        return None

    def set_elements(self, selector: str, elements: list[FakeElement]) -> None:
        self._elements_by_selector[selector] = elements

    def locator(self, selector: str) -> FakeLocator:
        if selector not in self._locators:
            self._locators[selector] = FakeLocator(
                selector,
                elements=list(self._elements_by_selector.get(selector, [FakeElement()])),
            )
        return self._locators[selector]

    def get_by_text(self, text: str, exact: bool = False) -> FakeLocator:
        return self.locator(f"text={text}")

    def get_by_role(self, role: str, name: str | None = None, exact: bool = False) -> FakeLocator:
        key = f"role={role}" + (f":{name}" if name else "")
        return self.locator(key)

    def on(self, event: str, handler: Any) -> None:
        if event == "download":
            self._download_listeners.append(handler)

    def remove_listener(self, event: str, handler: Any) -> None:
        if event == "download" and handler in self._download_listeners:
            self._download_listeners.remove(handler)

    def emit_download(self, download: Any) -> None:
        for handler in list(self._download_listeners):
            handler(download)


class FakeDownload:
    """Minimal Playwright download."""

    def __init__(self, suggested_filename: str, url: str) -> None:
        self.suggested_filename = suggested_filename
        self.url = url
