# Event Middleware
Middleware intercepts events before they reach subscribers. It is used for:
- Logging/Tracing.
- Data masking (e.g., stripping sensitive auth tokens).
- Rate-limiting high-frequency events (like DOM mutations).
