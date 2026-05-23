"""VCF Automation — cloud zones (``/iaas/api/zones``).

A cloud zone binds a region of a cloud account to a set of tags +
placement constraints. Projects then reference cloud zones in their
``zoneAssignmentConfigurations``.
"""

import requests

from saltext.vcf.utils import vcfa

_BASE = "/iaas/api/zones"


def list_(opts, profile=None):
    resp = vcfa.api_get(opts, _BASE, profile=profile)
    return resp.get("content", []) or []


def get(opts, zone_id, profile=None):
    return vcfa.api_get(opts, f"{_BASE}/{zone_id}", profile=profile)


def get_or_none(opts, zone_id, profile=None):
    try:
        return get(opts, zone_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, spec, profile=None):
    """Create a cloud zone.

    *spec* keys: ``name``, ``regionId``, ``placementPolicy``
    (``DEFAULT`` / ``SPREAD`` / ``BINPACK``), ``tags``,
    ``tagsToMatch``, ``customProperties``.
    """
    return vcfa.api_post(opts, _BASE, body=spec, profile=profile)


def update(opts, zone_id, spec, profile=None):
    return vcfa.api_patch(opts, f"{_BASE}/{zone_id}", body=spec, profile=profile)


def delete(opts, zone_id, profile=None):
    return vcfa.api_delete(opts, f"{_BASE}/{zone_id}", profile=profile)


def computes(opts, zone_id, profile=None):
    """Return the computes currently bound to the zone."""
    return vcfa.api_get(opts, f"{_BASE}/{zone_id}/computes", profile=profile)
