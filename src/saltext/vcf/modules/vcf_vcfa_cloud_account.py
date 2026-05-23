"""Execution module for VCF Automation cloud accounts."""

from saltext.vcf.clients import vcfa_cloud_account as c

__virtualname__ = "vcf_vcfa_cloud_account"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List all cloud accounts.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_cloud_account.list_
    """
    return c.list_(__opts__, profile=profile)


def get(account_id, profile=None):
    """Get one cloud account by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_cloud_account.get <account_id>
    """
    return c.get(__opts__, account_id, profile=profile)


def get_or_none(account_id, profile=None):
    """Get one cloud account by id, or ``None`` on 404.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_cloud_account.get_or_none <account_id>
    """
    return c.get_or_none(__opts__, account_id, profile=profile)


def create_vsphere(spec, profile=None):
    """Create a vSphere cloud account.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_cloud_account.create_vsphere '{"name": "vc-prod", ...}'
    """
    return c.create_vsphere(__opts__, spec, profile=profile)


def update_vsphere(account_id, spec, profile=None):
    """Update a vSphere cloud account."""
    return c.update_vsphere(__opts__, account_id, spec, profile=profile)


def create_nsxt(spec, profile=None):
    """Create an NSX-T cloud account."""
    return c.create_nsxt(__opts__, spec, profile=profile)


def update_nsxt(account_id, spec, profile=None):
    """Update an NSX-T cloud account."""
    return c.update_nsxt(__opts__, account_id, spec, profile=profile)


def delete(account_id, profile=None):
    """Delete a cloud account.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_cloud_account.delete <account_id>
    """
    return c.delete(__opts__, account_id, profile=profile)


def regions(account_id, profile=None):
    """Return discovered regions for a cloud account."""
    return c.regions(__opts__, account_id, profile=profile)
