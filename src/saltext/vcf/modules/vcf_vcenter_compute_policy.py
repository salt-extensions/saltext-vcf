"""Execution module for vCenter compute policies (Tanzu / Workload Management)."""

from saltext.vcf.clients import vcenter_compute_policy as c

__virtualname__ = "vcf_vcenter_compute_policy"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List compute policies.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_compute_policy.list_
    """
    return c.list_(__opts__, profile=profile)


def get(policy_id, profile=None):
    """Return one compute policy.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_compute_policy.get <policy_id>
    """
    return c.get(__opts__, policy_id, profile=profile)


def create(capability, profile=None, **spec):
    """Create a compute policy.

    *capability* is the policy capability identifier — e.g.
    ``com.vmware.vcenter.compute.policies.capabilities.vm.vm_anti_affinity``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_compute_policy.create <capability> name=anti-affinity-prod
    """
    return c.create(__opts__, capability, profile=profile, **spec)


def delete(policy_id, profile=None):
    """Delete a compute policy.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_compute_policy.delete <policy_id>
    """
    return c.delete(__opts__, policy_id, profile=profile)
