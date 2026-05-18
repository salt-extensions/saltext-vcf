"""Client for vCenter appliance APIs under ``/api/appliance/``.

Covers the VAMI-equivalent REST surface: services, system version, health
summary, DNS, syslog forwarding.

Note: ``/api/appliance/health/system`` returns a JSON-encoded plain string
(e.g. ``"green"``) rather than a dict. ``utils/vcenter.api_get`` returns
that string verbatim; callers should not assume a dict shape.
"""

import requests

from saltext.vcf.utils import vcenter

# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

_SERVICES = "/api/appliance/services"


def services_list(opts, profile=None):
    """Return the dict of appliance services, keyed by service id."""
    return vcenter.api_get(opts, _SERVICES, profile=profile)


def services_get(opts, service, profile=None):
    return vcenter.api_get(opts, f"{_SERVICES}/{service}", profile=profile)


def services_get_or_none(opts, service, profile=None):
    try:
        return services_get(opts, service, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def services_start(opts, service, profile=None):
    return vcenter.api_post(
        opts, f"{_SERVICES}/{service}", params={"action": "start"}, profile=profile
    )


def services_stop(opts, service, profile=None):
    return vcenter.api_post(
        opts, f"{_SERVICES}/{service}", params={"action": "stop"}, profile=profile
    )


def services_restart(opts, service, profile=None):
    return vcenter.api_post(
        opts, f"{_SERVICES}/{service}", params={"action": "restart"}, profile=profile
    )


# ---------------------------------------------------------------------------
# System
# ---------------------------------------------------------------------------


def version(opts, profile=None):
    return vcenter.api_get(opts, "/api/appliance/system/version", profile=profile)


def health_system(opts, profile=None):
    """Return the overall health status string (e.g. ``"green"``)."""
    return vcenter.api_get(opts, "/api/appliance/health/system", profile=profile)


# ---------------------------------------------------------------------------
# DNS
# ---------------------------------------------------------------------------

_DNS = "/api/appliance/networking/dns/servers"


def dns_get(opts, profile=None):
    """Return ``{"mode": "is_static"|"dhcp", "servers": [...]}``."""
    return vcenter.api_get(opts, _DNS, profile=profile)


def dns_set(opts, servers, mode="is_static", profile=None):
    return vcenter.api_patch(
        opts, _DNS, body={"mode": mode, "servers": list(servers)}, profile=profile
    )


# ---------------------------------------------------------------------------
# Syslog forwarding
# ---------------------------------------------------------------------------

_SYSLOG = "/api/appliance/logging/forwarding"


def logging_forwarding_get(opts, profile=None):
    return vcenter.api_get(opts, _SYSLOG, profile=profile)


def logging_forwarding_set(opts, servers, profile=None):
    """Replace the syslog forwarding destination list.

    *servers* is a list of forwarder configs, each shaped like::

        {"hostname": "collector.example.com", "port": 514, "protocol": "UDP"}
    """
    return vcenter.api_patch(opts, _SYSLOG, body={"cfg_list": list(servers)}, profile=profile)
