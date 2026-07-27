"""Resource layer for NSX Tier-0 gateways (Policy API /infra/tier-0s)."""

import requests

from saltext.vcf.utils import nsx

PATH = "/policy/api/v1/infra/tier-0s"


def list_(opts, profile=None):
    return nsx.api_get(opts, PATH, profile=profile)


def get(opts, tier0, profile=None):
    return nsx.api_get(opts, f"{PATH}/{tier0}", profile=profile)


def get_or_none(opts, tier0, profile=None):
    try:
        return get(opts, tier0, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def _ls_path(tier0, locale_service, suffix):
    return f"{PATH}/{tier0}/locale-services/{locale_service}/{suffix}"


def bgp_get(opts, tier0, locale_service="default", profile=None):
    """Return the BGP config for a Tier-0 locale-service."""
    return nsx.api_get(opts, _ls_path(tier0, locale_service, "bgp"), profile=profile)


def bgp_set(opts, tier0, enabled, locale_service="default", profile=None, **extra):
    """PATCH the BGP config, at minimum setting ``enabled``."""
    body = {"enabled": bool(enabled)}
    body.update(extra)
    return nsx.api_patch(opts, _ls_path(tier0, locale_service, "bgp"), body=body, profile=profile)


def ospf_get(opts, tier0, locale_service="default", profile=None):
    """Return the OSPF config for a Tier-0 locale-service."""
    return nsx.api_get(opts, _ls_path(tier0, locale_service, "ospf"), profile=profile)


def ospf_set(opts, tier0, enabled, locale_service="default", profile=None, **extra):
    """PATCH the OSPF config, at minimum setting ``enabled``."""
    body = {"enabled": bool(enabled)}
    body.update(extra)
    return nsx.api_patch(opts, _ls_path(tier0, locale_service, "ospf"), body=body, profile=profile)


def multicast_get(opts, tier0, locale_service="default", profile=None):
    """Return the multicast config for a Tier-0 locale-service."""
    return nsx.api_get(opts, _ls_path(tier0, locale_service, "multicast"), profile=profile)


def multicast_set(opts, tier0, enabled, locale_service="default", profile=None, **extra):
    """PATCH the multicast config, at minimum setting ``enabled``."""
    body = {"enabled": bool(enabled)}
    body.update(extra)
    return nsx.api_patch(
        opts, _ls_path(tier0, locale_service, "multicast"), body=body, profile=profile
    )
