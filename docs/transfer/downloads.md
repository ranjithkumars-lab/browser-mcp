# Downloads
Downloads are intercepted via the Browser Core. When a download triggers, the `DownloadStrategy` handles the incoming stream, buffering it to the designated `download_path` while emitting `transfer.download.progress` events.
