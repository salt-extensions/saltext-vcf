"""Execution module for VCF Installer log bundle generation."""

from saltext.vcf.clients import installer_logs as c

__virtualname__ = "vcf_installer_logs"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List log bundles.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_installer_logs.list_
    """
    return c.list_(__opts__, profile=profile)


def get(bundle_id, profile=None):
    """Return one log bundle by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_installer_logs.get <bundle_id>
    """
    return c.get(__opts__, bundle_id, profile=profile)


def generate(profile=None, **spec):
    """Generate a new log bundle.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_installer_logs.generate
    """
    return c.generate(__opts__, profile=profile, **spec)


def delete(bundle_id, profile=None):
    """Delete a log bundle.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_installer_logs.delete <bundle_id>
    """
    return c.delete(__opts__, bundle_id, profile=profile)
