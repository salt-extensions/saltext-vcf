"""Execution module for VCF Operations for Logs (vRLI) appliance certificate.

Thin passthrough around :mod:`saltext.vcf.clients.vrli_certificate`.
"""

from saltext.vcf.clients import vrli_certificate as c

__virtualname__ = "vcf_vrli_certificate"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """Return every installed appliance certificate.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vrli_certificate.list_
    """
    return c.list_(__opts__, profile=profile)


def get(profile=None):
    """Return the currently-installed appliance certificate (or None)."""
    return c.get(__opts__, profile=profile)


def install(cert_pem, key_pem, chain_pem=None, profile=None):
    """Install a replacement appliance certificate.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vrli_certificate.install "$(cat leaf.pem)" "$(cat leaf.key)"
    """
    return c.install(__opts__, cert_pem, key_pem, chain_pem=chain_pem, profile=profile)


def serial_number(profile=None):
    """Return the hex serial number of the installed certificate."""
    return c.serial_number(__opts__, profile=profile)
