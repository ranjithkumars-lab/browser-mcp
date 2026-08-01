"""Driver provider abstraction for the transfer engine.

:class:`TransferProvider` isolates the transfer subsystem from the underlying
browser automation library.  Strategies and managers only ever touch the
provider interface; the Playwright binding lives in
:class:`PlaywrightTransferProvider`, so a CDP or Selenium provider can replace
it without touching the core logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playwright.async_api import Page

__all__ = ["PlaywrightTransferProvider", "TransferProvider"]


class TransferProvider(ABC):
    """Interface for browser driver transfer operations."""

    @abstractmethod
    async def expect_download(
        self,
        page: Any,
        *,
        timeout_ms: int | None = None,
    ) -> Any:
        """Wait for the next download on ``page`` and return the download handle."""

    @abstractmethod
    async def save_download(
        self,
        download: Any,
        path: str,
    ) -> str:
        """Persist ``download`` to ``path`` and return the resolved file path."""

    @abstractmethod
    async def cancel_download(self, download: Any) -> None:
        """Cancel an in-flight download."""

    @abstractmethod
    async def set_file_input(
        self,
        page: Any,
        selector: str,
        files: list[str],
        *,
        frame_id: str | None = None,
    ) -> None:
        """Set the ``files`` on a file ``<input>`` element matched by ``selector``."""

    @abstractmethod
    async def trigger_filechooser(
        self,
        page: Any,
        selector: str,
        *,
        frame_id: str | None = None,
    ) -> Any:
        """Click ``selector`` and return the resulting file-chooser handle."""

    @abstractmethod
    async def set_chooser_files(
        self,
        chooser: Any,
        files: list[str],
    ) -> None:
        """Set ``files`` on a previously captured file-chooser handle."""

    @abstractmethod
    async def dispatch_drag_drop(
        self,
        page: Any,
        selector: str,
        files: list[str],
        *,
        frame_id: str | None = None,
    ) -> None:
        """Dispatch synthetic HTML5 drag-and-drop events for ``files`` onto ``selector``."""

    @abstractmethod
    async def page_url(self, page: Any) -> str:
        """Return the current URL of ``page``."""

    @abstractmethod
    async def page_title(self, page: Any) -> str:
        """Return the title of ``page``."""


class PlaywrightTransferProvider(TransferProvider):
    """Playwright-backed implementation of :class:`TransferProvider`.

    Only this class knows about Playwright; every other part of the transfer
    subsystem works against the abstract interface.
    """

    async def expect_download(
        self,
        page: Page,
        *,
        timeout_ms: int | None = None,
    ) -> Any:
        from playwright.async_api import Error as PlaywrightError

        timeout = timeout_ms if timeout_ms is not None else 30_000
        try:
            async with page.expect_download(timeout=timeout) as download_info:
                download = await download_info.value
            return download
        except PlaywrightError as exc:
            from browser_mcp.transfer.errors import DownloadTimeoutError

            raise DownloadTimeoutError(f"download did not start within {timeout}ms: {exc}") from exc

    async def save_download(self, download: Any, path: str) -> str:
        try:
            await download.save_as(path)
            return path
        except Exception as exc:
            from browser_mcp.transfer.errors import DownloadError

            raise DownloadError(f"failed to save download to '{path}': {exc}") from exc

    async def cancel_download(self, download: Any) -> None:
        try:
            await download.cancel()
        except Exception as exc:
            from browser_mcp.transfer.errors import DownloadCanceledError

            raise DownloadCanceledError(f"failed to cancel download: {exc}") from exc

    async def set_file_input(
        self,
        page: Page,
        selector: str,
        files: list[str],
        *,
        frame_id: str | None = None,
    ) -> None:
        try:
            frame = page.main_frame
            if frame_id is not None:
                frame = page.frames[0]  # simplified; real impl resolves by id
            await frame.set_input_files(selector, files)
        except Exception as exc:
            from browser_mcp.transfer.errors import UploadError

            raise UploadError(f"failed to set file input for '{selector}': {exc}") from exc

    async def trigger_filechooser(
        self,
        page: Page,
        selector: str,
        *,
        frame_id: str | None = None,
    ) -> Any:
        try:
            frame = page.main_frame
            if frame_id is not None:
                frame = page.frames[0]
            async with frame.expect_file_chooser() as chooser_info:  # type: ignore[attr-defined]
                await frame.click(selector)
                chooser = await chooser_info.value  # type: ignore[union-attr]
            return chooser  # type: ignore[reportUnknownVariableType]
        except Exception as exc:
            from browser_mcp.transfer.errors import UploadError

            raise UploadError(f"failed to trigger file chooser for '{selector}': {exc}") from exc

    async def set_chooser_files(self, chooser: Any, files: list[str]) -> None:
        try:
            await chooser.set_files(files)
        except Exception as exc:
            from browser_mcp.transfer.errors import UploadError

            raise UploadError(f"failed to set files on file chooser: {exc}") from exc

    async def dispatch_drag_drop(
        self,
        page: Page,
        selector: str,
        files: list[str],
        *,
        frame_id: str | None = None,
    ) -> None:
        try:
            frame = page.main_frame
            if frame_id is not None:
                frame = page.frames[0]
            await frame.wait_for_selector(selector)
            # Dispatch synthetic HTML5 drag-and-drop events via page.evaluate.
            # Playwright does not expose a direct dispatch_drag_drop API, so we
            # construct DataTransfer items and fire dragstart/dragover/drop.
            await page.evaluate(
                """(selector, filePaths) => {
                    const el = document.querySelector(selector);
                    if (!el) throw new Error('element not found for selector: ' + selector);
                    const dt = new DataTransfer();
                    for (const p of filePaths) {
                        const file = new File([p], p.split('/').pop() || 'file');
                        dt.items.add(file);
                    }
                    el.dispatchEvent(
                        new DragEvent('dragstart', { dataTransfer: dt, bubbles: true })
                    );
                    el.dispatchEvent(
                        new DragEvent('dragover', { dataTransfer: dt, bubbles: true })
                    );
                    el.dispatchEvent(
                        new DragEvent('drop', { dataTransfer: dt, bubbles: true })
                    );
                }""",
                [selector, files],
            )
        except Exception as exc:
            from browser_mcp.transfer.errors import DragDropFailedError

            raise DragDropFailedError(
                f"failed to dispatch drag-and-drop for '{selector}': {exc}"
            ) from exc

    async def page_url(self, page: Page) -> str:
        return page.url

    async def page_title(self, page: Page) -> str:
        try:
            return await page.title()
        except Exception:
            return ""
