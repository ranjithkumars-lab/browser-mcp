# Phase 7 Implementation Plan — Download / Upload Engine (Refined Enterprise Architecture)

This document details the refined technical implementation plan for **Phase 7: Download / Upload Engine** (`src/browser_mcp/transfer/`) of the Enterprise Browser MCP Platform. 
In accordance with our **Vibe Coding Rules**, no code will be written until this implementation plan is approved.

---

## 1. Executive Summary & Design Principles

The **Download / Upload Engine** is a **Browser Core service** that provides high-reliability, async file transfer management. Like Authentication (Phase 6), it is injected directly into `PluginContext` so all current (Forms, Scraper) and future plugins leverage unified transfer capabilities.

### Key Architectural Commitments:
1. **Browser Core Service**: Injected into `PluginContext` alongside `BrowserManager`, `SessionManager`, `ElementEngine`, `AuthManager`, `Logger`, and `EventBus`.
2. **Provider Abstraction (`TransferProvider`)**: Insulates core transfer logic from Playwright `page.on("download")` and `filechooser` internals (`PlaywrightTransferProvider`).
3. **Strategy Registries**:
   - `DownloadStrategyRegistry`: `BrowserDownloadStrategy` (implemented), `HttpDownloadStrategy` (reserved), `BlobDownloadStrategy` (reserved).
   - `UploadStrategyRegistry`: `InputUploadStrategy`, `ChooserUploadStrategy`, `DragDropUploadStrategy`, `BufferUploadStrategy` (reserved).
4. **Lifecycle & Transfer State Manager (`TransferStateManager`)**: Manages transfer states (`Queued`, `Running`, `Paused`, `Completed`, `Failed`, `Cancelled`). Includes APIs for `browser.transfer.cancel`, `browser.transfer.pause` (reserved), `browser.transfer.resume` (reserved).
5. **Artifact System Integration**: Seamlessly routes large file downloads to the centralized `ArtifactStorage` system.
6. **Full Configuration Schema (`config.transfer.*`)**: Configurable download directory, max file size, allowed extensions, MIME types, checksum algorithm, collision strategy, and cleanup policy.
7. **Explicit Error & Event Hierarchy**: Inherits from `BrowserError` and emits `EventBus` domain events (`transfer.download.*`, `transfer.upload.*`).
8. **Standardized Response Model**: `TransferResponse` JSON schema returned by all transfer tools.

---

## 2. Directory & Component Layout

```text
src/browser_mcp/transfer/
├── __init__.py
├── manager.py            # TransferManager facade (orchestration)
├── provider.py           # TransferProvider interface & PlaywrightTransferProvider
├── registry.py           # TransferRegistry façade over download/upload registries
├── state.py              # TransferStateManager (lifecycle tracking & state transitions)
├── models.py             # TransferResponse, TransferStatus, TransferProgress, TransferItem
├── errors.py             # TransferError hierarchy
├── events.py             # Domain event helpers (transfer.download.*, transfer.upload.*)
│
├── downloads/            # Download Engine Subsystem
│   ├── __init__.py
│   ├── manager.py        # DownloadManager (orchestrates download strategies)
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base.py       # BaseDownloadStrategy ABC
│   │   ├── browser.py    # BrowserDownloadStrategy (Playwright download stream)
│   │   ├── http.py       # Reserved extension point
│   │   ├── blob.py       # Reserved extension point
│   │   └── registry.py   # DownloadStrategyRegistry
│   ├── integrity.py      # ChecksumVerifier (SHA-256, SHA-1, MD5)
│   └── naming.py         # FileNamingStrategy (collision prevention & auto-rename)
│
├── uploads/              # Upload Engine Subsystem
│   ├── __init__.py
│   ├── manager.py        # UploadManager (orchestrates upload strategies)
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base.py       # BaseUploadStrategy ABC
│   │   ├── input.py      # InputUploadStrategy (direct file input selector)
│   │   ├── chooser.py    # ChooserUploadStrategy (filechooser event handler)
│   │   ├── drag_drop.py  # DragDropUploadStrategy (synthetic HTML5 DataTransfer events)
│   │   ├── buffer.py     # Reserved extension point
│   │   └── registry.py   # UploadStrategyRegistry
│   └── validator.py      # FileValidator (size limit, extension/MIME validation)
│
└── tools.py              # MCP Tool definitions (browser.download, browser.upload, etc.)
```

---

## 3. Detailed Component Specifications

### 3.1. Configuration Schema (`config.transfer.*`)
- `download_directory`: Base directory for saved transfers (defaults to artifact storage directory).
- `max_file_size_bytes`: Maximum allowed transfer size (e.g. 500 MB default).
- `allowed_extensions`: List of allowed extensions (empty list = allow all).
- `allowed_mime_types`: List of allowed MIME types.
- `checksum_algorithm`: Default checksum algorithm (`sha256`).
- `collision_strategy`: Strategy for duplicate filenames (`auto_rename`, `overwrite`, `reject`).
- `cleanup_policy`: Policy for temporary transfer files (`on_completion`, `on_failure`, `manual`).

### 3.2. Error Hierarchy (`src/browser_mcp/transfer/errors.py`)
```python
BrowserError
└── TransferError
    ├── DownloadError
    │   ├── DownloadTimeoutError
    │   ├── DownloadCanceledError
    │   └── IntegrityVerificationError
    └── UploadError
        ├── FileNotFoundError
        ├── FileSizeExceededError
        ├── InvalidMimeTypeError
        └── DragDropFailedError
```

### 3.3. Transfer Response Schema (`src/browser_mcp/transfer/models.py`)
```json
{
  "success": true,
  "transfer_id": "xfers_12345",
  "tool_name": "browser.download",
  "session_id": "s1",
  "browser_id": "b1",
  "context_id": "c1",
  "page_id": "p1",
  "file_name": "report.pdf",
  "file_path": "/artifacts/xfers_12345/report.pdf",
  "file_size_bytes": 1048576,
  "mime_type": "application/pdf",
  "checksum": {
    "algorithm": "sha256",
    "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "verified": true
  },
  "status": "completed",
  "progress_percentage": 100.0,
  "duration_ms": 450.0,
  "error": null
}
```

### 3.4. Lifecycle APIs & MCP Tools (`src/browser_mcp/transfer/tools.py`)
- `browser.download`: Initiates or awaits file download.
- `browser.upload`: Uploads files via specified strategy (`input`, `chooser`, `drag_drop`).
- `browser.transfer.status`: Queries status/progress of active or finished transfer.
- `browser.transfer.cancel`: Cancels an active in-flight transfer.

---

## 4. Documentation Strategy (`docs/transfer/`)

Complete documentation suite under `docs/transfer/`:
- `docs/transfer/overview.md`
- `docs/transfer/architecture.md`
- `docs/transfer/downloads.md`
- `docs/transfer/uploads.md`
- `docs/transfer/security.md`
- `docs/transfer/examples.md`
- `docs/transfer/tools.md`

---

## 5. Verification Plan

1. **Unit Tests (`tests/unit/test_transfer_*.py`)**:
   - `DownloadStrategyRegistry` & `UploadStrategyRegistry` lookup & fallback.
   - `ChecksumVerifier` (SHA-256, SHA-1, MD5 verification & invalid checksum rejection).
   - `FileNamingStrategy` collision handling (`auto_rename`, `overwrite`, `reject`).
   - `FileValidator` size limit & MIME type enforcement.
   - `TransferStateManager` lifecycle state transitions & cancellation.
2. **Integration Tests (`tests/integration/test_transfer_integration.py`)**:
   - Simulated Playwright download stream capture and artifact storage routing.
   - Form input upload, filechooser dialog handler, and drag-and-drop DOM event dispatching.
   - Concurrent downloads and multi-session transfer isolation.
   - Verification of `TransferManager` via `PluginContext`.
3. **Static Analysis**:
   - `uv run pyright` (Target: 0 errors).
   - `uv run pytest` (Target: 100% green pass).
