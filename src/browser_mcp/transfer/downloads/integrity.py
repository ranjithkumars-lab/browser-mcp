"""Streaming checksum calculation and verification."""

from __future__ import annotations

import hashlib
from pathlib import Path

from browser_mcp.transfer.errors import IntegrityVerificationError
from browser_mcp.transfer.models import ChecksumAlgorithm, ChecksumResult


class ChecksumVerifier:
    """Calculate SHA-256, SHA-1, or MD5 checksums without loading files in memory."""

    def verify(
        self,
        path: str | Path,
        *,
        algorithm: ChecksumAlgorithm | str = ChecksumAlgorithm.SHA256,
        expected: str | None = None,
    ) -> ChecksumResult:
        algo = ChecksumAlgorithm(algorithm)
        digest = hashlib.new(algo.value)
        with Path(path).open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        actual = digest.hexdigest()
        verified = expected is None or actual.lower() == expected.lower()
        result = ChecksumResult(algorithm=algo, hash=actual, expected=expected, verified=verified)
        if not verified:
            raise IntegrityVerificationError(f"checksum mismatch for '{path}'")
        return result
