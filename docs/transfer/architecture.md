# Transfer Architecture
The architecture comprises:
- `TransferManager`: The main facade orchestrating all operations.
- `TransferStateManager`: Tracks progress of active, paused, or failed transfers.
- `DownloadStrategyRegistry` & `UploadStrategyRegistry`: Resolves the appropriate strategy for the requested transfer.
- `SecurityValidator`: Enforces allowed paths, file extensions, and max sizes.
