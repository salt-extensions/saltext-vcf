"""VCF Automation — storage profiles (``/iaas/api/storage-profiles``).

A storage profile defines disk type, IOPS limits, datastore selection,
and other VM disk placement rules. The vSphere-specific
``/storage-profiles-vsphere`` shape is the one used in VCF.
"""

import requests

from saltext.vcf.utils import vcfa

_BASE = "/iaas/api/storage-profiles"
_VSPHERE = "/iaas/api/storage-profiles-vsphere"


def list_(opts, profile=None):
    resp = vcfa.api_get(opts, _BASE, profile=profile)
    return resp.get("content", []) or []


def list_vsphere(opts, profile=None):
    resp = vcfa.api_get(opts, _VSPHERE, profile=profile)
    return resp.get("content", []) or []


def get(opts, profile_id, profile=None):
    return vcfa.api_get(opts, f"{_BASE}/{profile_id}", profile=profile)


def get_vsphere(opts, profile_id, profile=None):
    return vcfa.api_get(opts, f"{_VSPHERE}/{profile_id}", profile=profile)


def get_or_none(opts, profile_id, profile=None):
    try:
        return get(opts, profile_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create_vsphere(opts, spec, profile=None):
    """Create a vSphere storage profile.

    *spec* keys: ``name``, ``regionId``, ``defaultItem``,
    ``diskType``, ``provisioningType``, ``sharesLevel``, ``shares``,
    ``limitIops``, ``datastoreId``, ``storagePolicyId``, ``tags``.
    """
    return vcfa.api_post(opts, _VSPHERE, body=spec, profile=profile)


def update_vsphere(opts, profile_id, spec, profile=None):
    return vcfa.api_patch(opts, f"{_VSPHERE}/{profile_id}", body=spec, profile=profile)


def delete(opts, profile_id, profile=None):
    return vcfa.api_delete(opts, f"{_BASE}/{profile_id}", profile=profile)
