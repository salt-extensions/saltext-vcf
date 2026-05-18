"""NSX IPsec VPN — services + sessions + IKE/tunnel/DPD profiles.

Per-tier0 VPN service path is:
``/policy/api/v1/infra/tier-0s/{t0}/locale-services/{locale}/ipsec-vpn-services``.
Profiles are global under ``/policy/api/v1/infra/ipsec-vpn-*``.
"""

import requests

from saltext.vcf.utils import nsx

IKE_PROFILES = "/policy/api/v1/infra/ipsec-vpn-ike-profiles"
TUNNEL_PROFILES = "/policy/api/v1/infra/ipsec-vpn-tunnel-profiles"
DPD_PROFILES = "/policy/api/v1/infra/ipsec-vpn-dpd-profiles"


def _service_path(tier0, locale, service=None):
    base = f"/policy/api/v1/infra/tier-0s/{tier0}/locale-services/{locale}/ipsec-vpn-services"
    return f"{base}/{service}" if service else base


def _session_path(tier0, locale, service, session=None):
    base = (
        f"/policy/api/v1/infra/tier-0s/{tier0}/locale-services/{locale}"
        f"/ipsec-vpn-services/{service}/sessions"
    )
    return f"{base}/{session}" if session else base


def _per_id(path):
    def _list(opts, profile=None):
        return nsx.api_get(opts, path, profile=profile)

    def _get(opts, resource_id, profile=None):
        return nsx.api_get(opts, f"{path}/{resource_id}", profile=profile)

    def _get_or_none(opts, resource_id, profile=None):
        try:
            return _get(opts, resource_id, profile=profile)
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                return None
            raise

    def _delete(opts, resource_id, profile=None):
        return nsx.api_delete(opts, f"{path}/{resource_id}", profile=profile)

    return _list, _get, _get_or_none, _delete


# IKE profiles
list_ike_profiles, get_ike_profile, get_ike_profile_or_none, delete_ike_profile = _per_id(
    IKE_PROFILES
)


def create_ike_profile(opts, ike_profile, profile=None, **spec):
    body = {"display_name": spec.pop("display_name", ike_profile)}
    body.update(spec)
    return nsx.api_put(opts, f"{IKE_PROFILES}/{ike_profile}", body=body, profile=profile)


# Tunnel profiles
list_tunnel_profiles, get_tunnel_profile, get_tunnel_profile_or_none, delete_tunnel_profile = (
    _per_id(TUNNEL_PROFILES)
)


def create_tunnel_profile(opts, tunnel_profile, profile=None, **spec):
    body = {"display_name": spec.pop("display_name", tunnel_profile)}
    body.update(spec)
    return nsx.api_put(opts, f"{TUNNEL_PROFILES}/{tunnel_profile}", body=body, profile=profile)


# DPD profiles
list_dpd_profiles, get_dpd_profile, get_dpd_profile_or_none, delete_dpd_profile = _per_id(
    DPD_PROFILES
)


def create_dpd_profile(opts, dpd_profile, profile=None, **spec):
    body = {"display_name": spec.pop("display_name", dpd_profile)}
    body.update(spec)
    return nsx.api_put(opts, f"{DPD_PROFILES}/{dpd_profile}", body=body, profile=profile)


# VPN services (per-tier0, per-locale)


def list_services(opts, tier0, locale, profile=None):
    return nsx.api_get(opts, _service_path(tier0, locale), profile=profile)


def get_service(opts, tier0, locale, service, profile=None):
    return nsx.api_get(opts, _service_path(tier0, locale, service), profile=profile)


def get_service_or_none(opts, tier0, locale, service, profile=None):
    try:
        return get_service(opts, tier0, locale, service, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create_service(opts, tier0, locale, service, profile=None, **spec):
    body = {
        "resource_type": spec.pop("resource_type", "IPSecVpnService"),
        "display_name": spec.pop("display_name", service),
    }
    body.update(spec)
    return nsx.api_put(opts, _service_path(tier0, locale, service), body=body, profile=profile)


def delete_service(opts, tier0, locale, service, profile=None):
    return nsx.api_delete(opts, _service_path(tier0, locale, service), profile=profile)


# VPN sessions (per-service)


def list_sessions(opts, tier0, locale, service, profile=None):
    return nsx.api_get(opts, _session_path(tier0, locale, service), profile=profile)


def get_session(opts, tier0, locale, service, session, profile=None):
    return nsx.api_get(opts, _session_path(tier0, locale, service, session), profile=profile)


def get_session_or_none(opts, tier0, locale, service, session, profile=None):
    try:
        return get_session(opts, tier0, locale, service, session, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create_session(opts, tier0, locale, service, session, resource_type, profile=None, **spec):
    """*resource_type*: ``PolicyBasedIPSecVpnSession`` | ``RouteBasedIPSecVpnSession``."""
    body = {
        "resource_type": resource_type,
        "display_name": spec.pop("display_name", session),
    }
    body.update(spec)
    return nsx.api_put(
        opts, _session_path(tier0, locale, service, session), body=body, profile=profile
    )


def delete_session(opts, tier0, locale, service, session, profile=None):
    return nsx.api_delete(opts, _session_path(tier0, locale, service, session), profile=profile)
