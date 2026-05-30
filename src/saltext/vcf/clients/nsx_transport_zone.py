"""NSX Management API — transport zones."""

import requests

from saltext.vcf.utils import nsx

PATH = "/api/v1/transport-zones"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, zone_id, profile=None):
    return nsx.api_get(opts, f"{PATH}/{zone_id}", profile=profile)


def get_or_none(opts, zone_id, profile=None):
    try:
        return get(opts, zone_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def get_by_name(opts, name, profile=None):
    body = list_(opts, profile=profile)
    for zone in body.get("results") or []:
        if name in (zone.get("id"), zone.get("display_name")):
            return zone
    return None


def create(opts, name, zone_type, profile=None, **spec):
    body = {
        "display_name": spec.pop("display_name", name),
        "transport_type": zone_type,
    }
    body.update(spec)
    return nsx.api_post(opts, PATH, body=body, profile=profile)


def update(opts, zone_id, profile=None, **spec):
    return nsx.api_put(opts, f"{PATH}/{zone_id}", body=spec, profile=profile)


def delete(opts, zone_id, profile=None):
    return nsx.api_delete(opts, f"{PATH}/{zone_id}", profile=profile)
