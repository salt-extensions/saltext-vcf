"""vCenter VM Classes — sizing templates for Supervisor namespace VMs.

VM classes define CPU/memory/reservation profiles that a Supervisor
namespace can attach. The default catalog has 16 classes (best-effort
+ guaranteed × xsmall/small/medium/large/xlarge + a few extras).
"""

import requests

from saltext.vmware.utils import vcenter

PATH = "/api/vcenter/namespace-management/virtual-machine-classes"


def list_(opts, profile=None):
    return vcenter.api_get(opts, PATH, profile=profile)


def get(opts, class_id, profile=None):
    return vcenter.api_get(opts, f"{PATH}/{class_id}", profile=profile)


def get_or_none(opts, class_id, profile=None):
    try:
        return get(opts, class_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, class_spec, profile=None):
    """Create a VM class.

    *class_spec* per the vSphere REST API — typically::

        {
            "id": "my-class",
            "cpu_count": 4,
            "memory_MB": 8192,
            "cpu_reservation": 0,
            "memory_reservation": 0,
            "description": "...",
            "config_spec": {...},  # optional
        }
    """
    return vcenter.api_post(opts, PATH, body=class_spec, profile=profile)


def update(opts, class_id, class_spec, profile=None):
    return vcenter.api_patch(opts, f"{PATH}/{class_id}", body=class_spec, profile=profile)


def delete(opts, class_id, profile=None):
    return vcenter.api_delete(opts, f"{PATH}/{class_id}", profile=profile)
