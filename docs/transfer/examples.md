# Examples
```python
# Initiate a download
transfer_mgr = AppContext.get(TransferManager)
job = await transfer_mgr.start_download(url="...", destination="/safe/path")
```
