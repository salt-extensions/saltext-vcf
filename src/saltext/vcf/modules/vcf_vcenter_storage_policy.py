"""Execution module for vCenter storage policies."""

from saltext.vcf.clients import vcenter_storage_policy as c

__virtualname__ = "vcf_vcenter_storage_policy"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_storage_policy.list_

    """
    return c.list_(__opts__, profile=profile)


def get(policy, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_storage_policy.get <policy>

    """
    return c.get(__opts__, policy, profile=profile)


def get_by_name(name, profile=None):
    """Get by name.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_storage_policy.get_by_name <name>

    """
    return c.get_by_name(__opts__, name, profile=profile)


def create(name, constraints, description=None, profile=None):
    """Create.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_storage_policy.create my-policy '[{"tags": {"cat1": ["gold"]}}]'

    """
    return c.create(__opts__, name, constraints, description=description, profile=profile)


def update(name, constraints=None, description=None, profile=None):
    """Update.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_storage_policy.update my-policy description='updated'

    """
    return c.update(__opts__, name, constraints=constraints, description=description, profile=profile)


def delete(name, profile=None):
    """Delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_storage_policy.delete my-policy

    """
    return c.delete(__opts__, name, profile=profile)


def default_policy_get(datastore, profile=None):
    """Default policy get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_storage_policy.default_policy_get vsanDatastore

    """
    return c.default_policy_get(__opts__, datastore, profile=profile)


def default_policy_set(datastore, policy_name, profile=None):
    """Default policy set.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_storage_policy.default_policy_set vsanDatastore my-policy

    """
    return c.default_policy_set(__opts__, datastore, policy_name, profile=profile)
