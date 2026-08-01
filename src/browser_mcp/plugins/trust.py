from __future__ import annotations
import hashlib
from browser_mcp.plugins.errors import PluginSignatureError


class SignatureVerifier:
    def verify(self, content: bytes, signature: str | None, *, required: bool = False) -> bool:
        if signature is None:
            if required: raise PluginSignatureError("plugin signature is required")
            return True
        valid = signature.removeprefix("sha256:") == hashlib.sha256(content).hexdigest()
        if not valid: raise PluginSignatureError("plugin signature verification failed")
        return True
PluginTrustValidator = SignatureVerifier
