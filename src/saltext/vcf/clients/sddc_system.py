"""SDDC Manager system info + personalities (/v1/system, /v1/personalities)."""

import requests

from saltext.vcf.utils import sddc


def get_system(opts, profile=None):
    """Return the SDDC Manager system info: vcfInstanceName, max domains, etc."""
    return sddc.api_get(opts, "/v1/system", profile=profile)


def list_personalities(opts, profile=None):
    """List installed personalities (vSphere Lifecycle Manager images)."""
    return sddc.api_get(opts, "/v1/personalities", profile=profile)


def get_personality(opts, personality_id, profile=None):
    return sddc.api_get(opts, f"/v1/personalities/{personality_id}", profile=profile)


def get_personality_or_none(opts, personality_id, profile=None):
    try:
        return get_personality(opts, personality_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise
