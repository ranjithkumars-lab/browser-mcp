from __future__ import annotations
from fastapi import Header, HTTPException, Request
def get_engine(request: Request):
    return request.app.state.api_engine
async def require_api_key(request: Request, x_api_key: str | None = Header(default=None)) -> None:
    expected = request.app.state.api_config.api_key
    if expected and x_api_key != expected: raise HTTPException(status_code=401, detail="invalid API key")
