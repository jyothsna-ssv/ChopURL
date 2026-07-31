import ipaddress
from urllib.parse import urlsplit

from app.core.config import settings


def validate_destination_url(url: str) -> None:
    """Reject obvious local or configured blocked destinations."""
    parsed = urlsplit(url)
    hostname = (parsed.hostname or "").lower().rstrip(".")
    if not hostname:
        raise ValueError("URL must include a hostname")
    if parsed.username or parsed.password:
        raise ValueError("URLs with embedded credentials are not allowed")

    blocked_hosts = {host.lower().rstrip(".") for host in settings.BLOCKED_HOSTS}
    if hostname in blocked_hosts or any(hostname.endswith(f".{host}") for host in blocked_hosts):
        raise ValueError("This destination host is blocked")

    if hostname in {"localhost", "localhost.localdomain", "0.0.0.0"} or hostname.endswith(".local"):
        raise ValueError("Local destinations are not allowed")

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return

    if (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    ):
        raise ValueError("Private or reserved destinations are not allowed")
