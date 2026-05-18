"""Execution module for VCF Installer credential management."""

from saltext.vcf.clients import installer_credentials as c

__virtualname__ = "vcf_installer_credentials"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List managed credentials.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_installer_credentials.list_
    """
    return c.list_(__opts__, profile=profile)


def get(password_id, profile=None):
    """Return one credential record by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_installer_credentials.get <password_id>
    """
    return c.get(__opts__, password_id, profile=profile)


def rotate(password_id, new_password, profile=None):
    """Rotate a managed credential.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_installer_credentials.rotate <password_id> <new_password>
    """
    return c.rotate(__opts__, password_id, new_password, profile=profile)
