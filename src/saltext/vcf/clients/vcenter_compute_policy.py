"""vCenter Compute Policy (`/api/vcenter/vm/compute/policies`).

Compute policies are Tanzu / Workload Management constructs that influence
DRS placement decisions for VMs and pods (VM-VM affinity, VM-host affinity,
disk + capacity policies). Terraform exposes ``vsphere_compute_policy``.
"""

import requests

from saltext.vcf.utils import vcenter

PATH = "/api/vcenter/vm/compute/policies"


def list_(opts, profile=None):
    return vcenter.api_get(opts, PATH, profile=profile)


def get(opts, policy_id, profile=None):
    return vcenter.api_get(opts, f"{PATH}/{policy_id}", profile=profile)


def get_or_none(opts, policy_id, profile=None):
    try:
        return get(opts, policy_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, capability, profile=None, **spec):
    """Create a compute policy.

    *capability* identifies the policy type, e.g.::

        com.vmware.vcenter.compute.policies.capabilities.vm.vm_affinity
        com.vmware.vcenter.compute.policies.capabilities.vm.vm_anti_affinity
        com.vmware.vcenter.compute.policies.capabilities.vm.vm_host_affinity
        com.vmware.vcenter.compute.policies.capabilities.disable_drs_vmotion
    """
    body = {"capability": capability}
    body.update(spec)
    return vcenter.api_post(opts, PATH, body=body, profile=profile)


def delete(opts, policy_id, profile=None):
    return vcenter.api_delete(opts, f"{PATH}/{policy_id}", profile=profile)
