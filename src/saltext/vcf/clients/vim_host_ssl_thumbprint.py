"""Fetch and validate ESXi SSL certificate thumbprints.

``fetch`` opens a raw TLS connection (no SOAP); ``current`` reads the
thumbprint vCenter knows about; ``validate`` compares them.
"""

import socket
import ssl

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _host(opts, host_id_or_name, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True)
    try:
        for host in container.view:
            if host_id_or_name in (host._moId, host.name):  # noqa: SLF001
                return host
    finally:
        container.Destroy()
    raise LookupError(f"host {host_id_or_name!r} not found")


def fetch(hostname, port=443, timeout=10):
    """Return the SHA-1 thumbprint of *hostname:port*'s SSL certificate, colon-separated.

    No SOAP required. Used for pre-vCenter-add validation and drift checks.
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with socket.create_connection((hostname, port), timeout=timeout) as sock:
        with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
            der = ssock.getpeercert(binary_form=True)
    import hashlib

    digest = hashlib.sha1(der, usedforsecurity=False).hexdigest().upper()  # nosec B324
    return ":".join(digest[i : i + 2] for i in range(0, len(digest), 2))


def current(opts, host, profile=None):
    """Return the thumbprint vCenter has cached for *host*."""
    h = _host(opts, host, profile=profile)
    info = getattr(h.summary.config, "sslThumbprint", None)
    return info


def validate(opts, host, profile=None):
    """Fetch the live thumbprint and compare against the one vCenter knows.

    Returns ``{current, live, match}``. If the host's management address is
    unreachable, ``live`` is ``None`` and ``match`` is ``False``.
    """
    h = _host(opts, host, profile=profile)
    cur = getattr(h.summary.config, "sslThumbprint", None)
    address = h.name
    try:
        live = fetch(address)
    except OSError:
        live = None
    return {"current": cur, "live": live, "match": bool(cur and live and cur == live)}
