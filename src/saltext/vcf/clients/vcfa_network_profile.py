"""VCF Automation — deploy network profiles (``/iaas/api/network-profiles``).

Network profiles define the network selection rules + fabric-network
bindings VCFA uses at deploy time.
"""

import requests

from saltext.vcf.utils import vcfa

_BASE = "/iaas/api/network-profiles"


def list_(opts, profile=None):
    resp = vcfa.api_get(opts, _BASE, profile=profile)
    return resp.get("content", []) or []


def get(opts, profile_id, profile=None):
    return vcfa.api_get(opts, f"{_BASE}/{profile_id}", profile=profile)


def get_or_none(opts, profile_id, profile=None):
    try:
        return get(opts, profile_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, spec, profile=None):
    """Create a network profile.

    *spec* keys: ``name``, ``regionId``, ``isolationType``,
    ``isolationNetworkDomainCIDR``, ``isolationNetworkDomainId``,
    ``isolationExternalFabricNetworkId``, ``fabricNetworkIds``,
    ``securityGroupIds``, ``loadBalancerIds``, ``tags``.
    """
    return vcfa.api_post(opts, _BASE, body=spec, profile=profile)


def update(opts, profile_id, spec, profile=None):
    return vcfa.api_patch(opts, f"{_BASE}/{profile_id}", body=spec, profile=profile)


def delete(opts, profile_id, profile=None):
    return vcfa.api_delete(opts, f"{_BASE}/{profile_id}", profile=profile)
