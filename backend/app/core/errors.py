class LinkNotFoundError(Exception):
    """Raised when a requested short link does not exist."""


class LinkOwnershipError(Exception):
    """Raised when a caller attempts to manage another user's link."""


class LinkValidationError(ValueError):
    """A validation failure with a client-safe message."""


class ShortCodeConflictError(Exception):
    """Raised when a custom short code has already been reserved."""


class ShortCodeGenerationError(Exception):
    """Raised when generated-code collision retries are exhausted."""
