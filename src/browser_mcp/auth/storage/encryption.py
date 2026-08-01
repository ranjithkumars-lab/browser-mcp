"""AES-256-GCM encryption for persisted auth states."""

from __future__ import annotations

import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from browser_mcp.errors import StateSaveError

__all__ = ["AuthEncryptionEngine"]


class AuthEncryptionEngine:
    """AES-256-GCM encryption with configurable key and plaintext fallback."""

    _key: bytes

    def __init__(self, key: str | None = None, *, allow_plaintext: bool = False) -> None:
        self._allow_plaintext = allow_plaintext
        if key is not None:
            raw = key.encode("utf-8")
            self._key = raw[:32].ljust(32, b"\x00")
        else:
            self._key = os.urandom(32)
        self._aesgcm = AESGCM(self._key)

    def encrypt(self, plaintext: str) -> bytes:
        if self._allow_plaintext and not self._key:
            return plaintext.encode("utf-8")
        nonce = os.urandom(12)
        ct = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return nonce + ct

    def decrypt(self, payload: bytes) -> str:
        if self._allow_plaintext and not self._key:
            return payload.decode("utf-8")
        try:
            nonce = payload[:12]
            ct = payload[12:]
            pt = self._aesgcm.decrypt(nonce, ct, None)
            return pt.decode("utf-8")
        except Exception as exc:
            raise StateSaveError(f"failed to decrypt auth state: {exc}") from exc