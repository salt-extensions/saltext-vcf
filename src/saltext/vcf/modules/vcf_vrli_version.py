"""Execution module for the vRLI product version endpoint."""

from saltext.vcf.clients import vrli_version as c

__virtualname__ = "vcf_vrli_version"


def __virtual__():
    return __virtualname__


def get(profile=None):
    """Return ``{"releaseName": "...", "version": "..."}``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vrli_version.get
    """
    return c.get(__opts__, profile=profile)
