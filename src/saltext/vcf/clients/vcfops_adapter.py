"""VCF Operations — adapter kinds and adapter instances.

Adapter *kinds* (``/suite-api/api/adapterkinds``) describe the *types* of
adapters VCF Operations supports (VMWARE, NSXTADAPTER, EP Ops, etc.).

Adapter *instances* (``/suite-api/api/adapters``) are the actual, configured
connections to concrete targets (a specific vCenter, a specific NSX manager,
etc.) that bind an adapter kind to a credential and a collector.
"""

import requests

from saltext.vcf.utils import vcfops

PATH = "/suite-api/api/adapterkinds"
_INSTANCES = "/suite-api/api/adapters"


def list_(opts):
    return vcfops.api_get(opts, PATH)


def get(opts, kind_key):
    return vcfops.api_get(opts, f"{PATH}/{kind_key}")


def get_or_none(opts, kind_key):
    try:
        return get(opts, kind_key)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def instance_list(opts, profile=None):
    """List every configured adapter instance."""
    return vcfops.api_get(opts, _INSTANCES, profile=profile)


def instance_get(opts, instance_id, profile=None):
    """Get a single adapter instance by id."""
    return vcfops.api_get(opts, f"{_INSTANCES}/{instance_id}", profile=profile)


def instance_get_or_none(opts, instance_id, profile=None):
    """Return the adapter instance or ``None`` if it 404s."""
    try:
        return instance_get(opts, instance_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def instance_create(opts, spec, profile=None):
    """Create an adapter instance.

    *spec* example::

        {
            "name": "vcenter-prod",
            "adapterKindKey": "VMWARE",
            "resourceIdentifiers": [
                {"name": "VCURL", "value": "https://vc.example.test"},
            ],
            "credentialInstanceId": "abc-123",
            "collectorId": 1,
        }
    """
    return vcfops.api_post(opts, _INSTANCES, body=spec, profile=profile)


def instance_update(opts, instance_id, spec, profile=None):
    """Update an existing adapter instance."""
    return vcfops.api_put(opts, f"{_INSTANCES}/{instance_id}", body=spec, profile=profile)


def instance_delete(opts, instance_id, profile=None):
    """Delete an adapter instance."""
    return vcfops.api_delete(opts, f"{_INSTANCES}/{instance_id}", profile=profile)


def instance_start(opts, instance_id, profile=None):
    """Start monitoring on an adapter instance."""
    return vcfops.api_post(
        opts, f"{_INSTANCES}/{instance_id}/monitoringstate/start", profile=profile
    )


def instance_stop(opts, instance_id, profile=None):
    """Stop monitoring on an adapter instance."""
    return vcfops.api_post(
        opts, f"{_INSTANCES}/{instance_id}/monitoringstate/stop", profile=profile
    )
