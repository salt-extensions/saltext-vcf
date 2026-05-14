"""Execution module for ESXi SSL thumbprint fetch/validate."""

from saltext.vmware.clients import vim_host_ssl_thumbprint as c

__virtualname__ = "vmware_vim_host_ssl_thumbprint"


def __virtual__():
    return __virtualname__


def fetch(hostname, port=443, timeout=10):
    """Open a raw TLS connection to *hostname:port* and return the SHA-1 thumbprint.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_ssl_thumbprint.fetch <hostname>

    """
    return c.fetch(hostname, port=int(port), timeout=int(timeout))


def current(host, profile=None):
    """Return the thumbprint vCenter has cached for *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_ssl_thumbprint.current <host>

    """
    return c.current(__opts__, host, profile=profile)


def validate(host, profile=None):
    """Compare the host's live thumbprint with the one vCenter knows about.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_host_ssl_thumbprint.validate <host>

    """
    return c.validate(__opts__, host, profile=profile)
