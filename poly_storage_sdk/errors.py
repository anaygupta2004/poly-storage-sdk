from __future__ import annotations

from typing import Any, Optional


class PolyStorageError(Exception):
    """Base exception for SDK errors."""


class PolyStorageAPIError(PolyStorageError):
    """Raised for non-success API responses."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        detail: Optional[str] = None,
        response_body: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail
        self.response_body = response_body


class PolyStorageAuthError(PolyStorageAPIError):
    """Raised for authentication and authorization failures."""
