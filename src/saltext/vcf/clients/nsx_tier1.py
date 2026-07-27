"""Resource layer for NSX Tier-1 gateways (Policy API /infra/tier-1s)."""

import requests

from saltext.vcf.utils import nsx

PATH = "/policy/api/v1/infra/tier-1s"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, tier1, profile=None):
    return nsx.api_get(opts, f"{PATH}/{tier1}", profile=profile)


def get_or_none(opts, tier1, profile=None):
    try:
        return get(opts, tier1, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, tier1, profile=None, **spec):
    body = {"display_name": spec.pop("display_name", tier1)}
    body.update(spec)
    return nsx.api_put(opts, f"{PATH}/{tier1}", body=body, profile=profile)


def delete(opts, tier1, profile=None):
    return nsx.api_delete(opts, f"{PATH}/{tier1}", profile=profile)


def _ls_path(tier1, locale_service, suffix):
    return f"{PATH}/{tier1}/locale-services/{locale_service}/{suffix}"


def multicast_get(opts, tier1, locale_service="default", profile=None):
    """Return the multicast config for a Tier-1 locale-service."""
    return nsx.api_get(opts, _ls_path(tier1, locale_service, "multicast"), profile=profile)


def multicast_set(opts, tier1, enabled, locale_service="default", profile=None, **extra):
    """PATCH the multicast config, at minimum setting ``enabled``."""
    body = {"enabled": bool(enabled)}
    body.update(extra)
    return nsx.api_patch(
        opts, _ls_path(tier1, locale_service, "multicast"), body=body, profile=profile
    )
