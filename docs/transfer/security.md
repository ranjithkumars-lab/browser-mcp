# Transfer Security
- **Path Traversal**: All paths are resolved against a strict `workspace_root`.
- **MIME Validation**: Files are checked against an allowed list (e.g., PDFs, CSVs, Images).
- **Size Limits**: Hard caps prevent memory overflow and disk exhaustion.
