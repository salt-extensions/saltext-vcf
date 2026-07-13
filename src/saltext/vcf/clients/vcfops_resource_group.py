"""VCF Operations — custom resource groups.

A resource group is a saved query / static-or-dynamic membership list
that scopes metrics, alerts, and policies. The lab ships 17 default
groups (e.g. "vSphere Cluster Compute Resources").
"""

import requests

from saltext.vcf.utils import vcfops

_PATH = "/suite-api/api/resources/groups"


def list_(opts, profile=None):
    return vcfops.api_get(opts, _PATH, profile=profile)


def get(opts, group_id, profile=None):
    return vcfops.api_get(opts, f"{_PATH}/{group_id}", profile=profile)


def get_or_none(opts, group_id, profile=None):
    try:
        return get(opts, group_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, group_spec, profile=None):
    """Create a resource group.

    *group_spec* example::

        {"resourceKey": {"name": "my-vms", "adapterKindKey": "VMWARE",
                          "resourceKindKey": "VirtualMachine"},
         "membershipDefinition": {"includedResources": [...]}}
    """
    return vcfops.api_post(opts, _PATH, body=group_spec, profile=profile)


def update(opts, group_id, group_spec, profile=None):
    return vcfops.api_put(opts, f"{_PATH}/{group_id}", body=group_spec, profile=profile)


def delete(opts, group_id, profile=None):
    return vcfops.api_delete(opts, f"{_PATH}/{group_id}", profile=profile)


def members(opts, group_id, profile=None):
    """List the resources currently matched by a resource group."""
    return vcfops.api_get(opts, f"{_PATH}/{group_id}/members", profile=profile)


def list_types(opts, profile=None):
    """List the group-kind types available for resource groups."""
    return vcfops.api_get(opts, f"{_PATH}/types", profile=profile)
