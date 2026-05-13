"""NSX L2 VPN — services + sessions.

L2 VPN extends a layer-2 segment across sites. Like IPsec VPN it has a
per-tier-0 service plus per-service sessions, but the API surface is
independent (and the data model is different — L2 sessions bind a
``transport_tunnel_path`` referencing an existing IPsec session).

Per-tier0 service path:
``/policy/api/v1/infra/tier-0s/{t0}/locale-services/{locale}/l2vpn-services``.
"""

import requests

from saltext.vmware.utils import nsx


def _service_path(tier0, locale, service=None):
    base = f"/policy/api/v1/infra/tier-0s/{tier0}/locale-services/{locale}/l2vpn-services"
    return f"{base}/{service}" if service else base


def _session_path(tier0, locale, service, session=None):
    base = (
        f"/policy/api/v1/infra/tier-0s/{tier0}/locale-services/{locale}"
        f"/l2vpn-services/{service}/sessions"
    )
    return f"{base}/{session}" if session else base


# Services


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
        "resource_type": spec.pop("resource_type", "L2VPNService"),
        "display_name": spec.pop("display_name", service),
    }
    body.update(spec)
    return nsx.api_put(opts, _service_path(tier0, locale, service), body=body, profile=profile)


def delete_service(opts, tier0, locale, service, profile=None):
    return nsx.api_delete(opts, _service_path(tier0, locale, service), profile=profile)


# Sessions


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


def create_session(opts, tier0, locale, service, session, profile=None, **spec):
    """*spec* should include ``transport_tunnels`` (list of IPsec session paths)
    and ``direction`` (``BOTH`` typical for site-to-site L2VPN).
    """
    body = {
        "resource_type": spec.pop("resource_type", "L2VPNSession"),
        "display_name": spec.pop("display_name", session),
    }
    body.update(spec)
    return nsx.api_put(
        opts, _session_path(tier0, locale, service, session), body=body, profile=profile
    )


def delete_session(opts, tier0, locale, service, session, profile=None):
    return nsx.api_delete(opts, _session_path(tier0, locale, service, session), profile=profile)
