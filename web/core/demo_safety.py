"""Guards for the disposable mobile demo (QA-2026-10-22-10).

The demo runs with DEBUG, so it must never sign with a versioned key nor
listen on a public address.
"""

import ipaddress
import secrets

from django.core.exceptions import ImproperlyConfigured


def demo_secret_key(path):
    """Random per-installation key kept next to the demo database (git-ignored)."""
    if not path.exists():
        path.write_text(secrets.token_urlsafe(50), encoding="utf-8")
    return path.read_text(encoding="utf-8").strip()


def private_hosts(raw):
    """Extra hosts from VIGIA_DEMO_HOSTS: only loopback or private (RFC 1918) IPs."""
    hosts = [host.strip() for host in (raw or "").split(",") if host.strip()]
    for host in hosts:
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            raise ImproperlyConfigured(
                f"VIGIA_DEMO_HOSTS solo admite IP locales o privadas; «{host}» no lo es."
            ) from None
        if not (address.is_loopback or address.is_private) or address.is_unspecified:
            raise ImproperlyConfigured(
                f"VIGIA_DEMO_HOSTS solo admite IP locales o privadas; «{host}» no lo es."
            )
    return hosts
