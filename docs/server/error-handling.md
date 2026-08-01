# Error Handling
`BrowserError` subclasses are deterministically mapped to JSON-RPC codes:
- `NavigationError` -> `-32600` (InvalidRequest)
- `AuthenticationError` -> `-32001`
