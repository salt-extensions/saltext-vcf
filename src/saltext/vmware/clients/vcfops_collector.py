"""VCF Operations — data collectors and collector groups.

Collectors are the data-plane workers that pull telemetry from
adapters (vCenter, NSX, ESXi, ...) and forward it to the analytics
engine. Collector groups bind logical adapter assignments to a pool
of collectors for resilience.
"""

import requests

from saltext.vmware.utils import vcfops

_COLLECTORS = "/suite-api/api/collectors"
_GROUPS = "/suite-api/api/collectorgroups"


def list_(opts, profile=None):
    """List every registered collector."""
    return vcfops.api_get(opts, _COLLECTORS, profile=profile)


def get(opts, collector_id, profile=None):
    return vcfops.api_get(opts, f"{_COLLECTORS}/{collector_id}", profile=profile)


def get_or_none(opts, collector_id, profile=None):
    try:
        return get(opts, collector_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def delete(opts, collector_id, profile=None):
    return vcfops.api_delete(opts, f"{_COLLECTORS}/{collector_id}", profile=profile)


def groups_list(opts, profile=None):
    return vcfops.api_get(opts, _GROUPS, profile=profile)


def groups_get(opts, group_id, profile=None):
    return vcfops.api_get(opts, f"{_GROUPS}/{group_id}", profile=profile)


def groups_get_or_none(opts, group_id, profile=None):
    try:
        return groups_get(opts, group_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def groups_create(opts, group_spec, profile=None):
    """Create a collector group.

    *group_spec* example::

        {"name": "primary", "description": "...", "collectorId": [12345]}
    """
    return vcfops.api_post(opts, _GROUPS, body=group_spec, profile=profile)


def groups_update(opts, group_id, group_spec, profile=None):
    return vcfops.api_put(opts, f"{_GROUPS}/{group_id}", body=group_spec, profile=profile)


def groups_delete(opts, group_id, profile=None):
    return vcfops.api_delete(opts, f"{_GROUPS}/{group_id}", profile=profile)
