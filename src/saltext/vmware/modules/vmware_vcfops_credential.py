"""Execution module for VCF Operations stored credentials."""

from saltext.vmware.clients import vcfops_credential as c

__virtualname__ = "vmware_vcfops_credential"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_credential.list_

    """
    return c.list_(__opts__, profile=profile)


def get(credential_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_credential.get <credential_id>

    """
    return c.get(__opts__, credential_id, profile=profile)


def create(credential_spec, profile=None):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_credential.create <credential_spec>

    """
    return c.create(__opts__, credential_spec, profile=profile)


def update(credential_id, credential_spec, profile=None):
    """Update.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_credential.update <credential_id> <credential_spec>

    """
    return c.update(__opts__, credential_id, credential_spec, profile=profile)


def delete(credential_id, profile=None):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_credential.delete <credential_id>

    """
    return c.delete(__opts__, credential_id, profile=profile)


def kinds_list(profile=None):
    """Kinds list.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcfops_credential.kinds_list

    """
    return c.kinds_list(__opts__, profile=profile)
