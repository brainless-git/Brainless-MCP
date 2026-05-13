"""Custom exceptions for Brainless MCP."""


class UnraidError(Exception):
    """Base error for all Unraid API failures."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class UnraidAuthError(UnraidError):
    """Authentication / authorisation failure."""


class UnraidNotFoundError(UnraidError):
    """Requested resource not found."""


class UnraidRateLimitError(UnraidError):
    """Rate limit exceeded."""


class ConfirmationRequired(UnraidError):
    """Destructive action attempted without confirm=True."""
