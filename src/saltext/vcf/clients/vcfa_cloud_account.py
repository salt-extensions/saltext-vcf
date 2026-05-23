"""VCF Automation — cloud accounts (``/iaas/api/cloud-accounts``).

A cloud account is VCFA's stored binding to a provider (vSphere, NSX,
AWS, Azure, GCP, VMC). The provider determines the ``create_*`` /
``update_*`` endpoint shape; this client exposes the generic
read/delete and the vSphere + NSX-T create paths, which are the two
that matter for VCF.
"""

import requests

from saltext.vcf.utils import vcfa

_BASE = "/iaas/api/cloud-accounts"
_VSPHERE = "/iaas/api/cloud-accounts-vsphere"
_NSXT = "/iaas/api/cloud-accounts-nsx-t"


def list_(opts, profile=None):
    """Return the ``content`` list of all cloud accounts."""
    resp = vcfa.api_get(opts, _BASE, profile=profile)
    return resp.get("content", []) or []


def get(opts, account_id, profile=None):
    return vcfa.api_get(opts, f"{_BASE}/{account_id}", profile=profile)


def get_or_none(opts, account_id, profile=None):
    try:
        return get(opts, account_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create_vsphere(opts, spec, profile=None):
    """Create a vSphere cloud account.

    *spec* must include ``name``, ``hostName``, ``username``, ``password``,
    ``acceptSelfSignedCertificate``, ``regions``, and ``dcid`` (data
    collector / cloud proxy id).
    """
    return vcfa.api_post(opts, _VSPHERE, body=spec, profile=profile)


def update_vsphere(opts, account_id, spec, profile=None):
    return vcfa.api_patch(opts, f"{_VSPHERE}/{account_id}", body=spec, profile=profile)


def create_nsxt(opts, spec, profile=None):
    """Create an NSX-T cloud account.

    *spec* must include ``name``, ``hostName``, ``username``, ``password``,
    ``associatedCloudAccountIds`` (the vSphere accounts this NSX-T pairs
    with).
    """
    return vcfa.api_post(opts, _NSXT, body=spec, profile=profile)


def update_nsxt(opts, account_id, spec, profile=None):
    return vcfa.api_patch(opts, f"{_NSXT}/{account_id}", body=spec, profile=profile)


def delete(opts, account_id, profile=None):
    return vcfa.api_delete(opts, f"{_BASE}/{account_id}", profile=profile)


def regions(opts, account_id, profile=None):
    """Return the list of discovered regions for the cloud account."""
    return vcfa.api_get(opts, f"{_BASE}/{account_id}/regions", profile=profile)
