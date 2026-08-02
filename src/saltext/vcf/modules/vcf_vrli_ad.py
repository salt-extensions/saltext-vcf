"""Execution module for VCF Operations for Logs (vRLI) AD integration.

Thin passthrough around :mod:`saltext.vcf.clients.vrli_ad`.
"""

from saltext.vcf.clients import vrli_ad as c

__virtualname__ = "vcf_vrli_ad"


def __virtual__():
    return __virtualname__


def get(profile=None):
    """Return the current AD configuration.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vrli_ad.get
    """
    return c.get(__opts__, profile=profile)


def set_(spec, profile=None):
    """Apply an AD configuration.

    *spec* keys: ``enableAD`` (bool), ``domain``, ``username``,
    ``password``, ``connType`` (``STANDARD`` | ``GLOBAL_CAT`` |
    ``CUSTOM``). Every field is required when enabling AD.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vrli_ad.set_ '{"enableAD": true, "domain": "corp.example.com", ...}'
    """
    return c.set_(__opts__, spec, profile=profile)


def disable(profile=None):
    """Disable AD integration (POST enableAD:false)."""
    return c.disable(__opts__, profile=profile)
