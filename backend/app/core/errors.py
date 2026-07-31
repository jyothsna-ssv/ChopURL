class LinkNotFoundError(Exception):
    """Raised when a requested short link does not exist."""


class LinkOwnershipError(Exception):
    """Raised when a caller attempts to manage another user's link."""
