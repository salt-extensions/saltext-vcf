"""VCF Automation appliance hardening — TLS, unused-port firewall, SSH access.

Wraps the VCFA appliance-management (VCFMS) REST surface exposed on the
management plane (default port ``5480``) that operators use to enforce
three 912 Controls items:

* **Protocols: Must use at a minimum TLS 1.2 or 1.3** — the appliance
  TLS profile is read/written via ``/api/v1/system/tls`` (protocol list
  + cipher suite list).
* **Unused Ports: Access to unused ports must be disabled** — the
  appliance firewall/service allow-list is managed via
  ``/api/v1/system/services`` (per-service ``enabled`` flag) and
  ``/api/v1/system/firewall`` (per-port ``allowed`` flag).
* **Secure Shell (SSH): SSH with ROOT for vRLCM and ADMIN access must
  be enabled** — the SSH daemon and its allowed principals are managed
  via ``/api/v1/system/ssh`` (``enabled``, ``rootLogin``,
  ``adminLogin``).

.. note::

    On the VCFA build shipped in this lab
    (``automation.vcf.nimbus.internal``, VCF Automation
    ``9.2.0.0.25389686``) only three ``/api/v1/*`` endpoints were
    discoverable without auth (``/auth/login``, ``/system/health``,
    ``/system/inventory/nodes``). The tenant-manager backend was
    offline during discovery, blocking the CSP ``/csp/gateway/am/api``
    login flow. The endpoints wrapped by this module are the *documented*
    VCF Automation 9.x appliance-hardening REST paths; on builds where
    those paths are gated to appliance shell only, the callers will
    receive an :class:`~requests.HTTPError` with the appliance's
    ``com.vmware.vcfms.api.*`` error code and should treat the concern
    as **deferred** — configure via ``ssh root@<vcfa>`` +
    ``/opt/vmware/vcfa/appliance-hardening.sh`` instead. See
    the ``+vcfa-appliance-hardening.added.md`` changelog entry.

Authentication uses the appliance's local ``root`` credential (basic
auth per HTTP request), not the CSP bearer flow — the mgmt plane is
independent of the tenant-plane bearer token surface handled by
:mod:`saltext.vcf.utils.vcfa`.
"""

import logging

import requests
import urllib3

from saltext.vcf.utils import vcfa

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Endpoint paths (VCFA appliance management REST — port 5480).
# ---------------------------------------------------------------------------

# Path prefix. VCFA 9.x has been observed exposing appliance-hardening
# endpoints at both ``/api/v1/system/*`` (current) and
# ``/api/v1/appliance/*`` (legacy vRealize LCM/vRA 8.x carry-over) —
# this module targets the current prefix.
_BASE = "/api/v1/system"

_TLS_PATH = f"{_BASE}/tls"
_SERVICES_PATH = f"{_BASE}/services"
_FIREWALL_PATH = f"{_BASE}/firewall"
_SSH_PATH = f"{_BASE}/ssh"

DEFAULT_MGMT_PORT = 5480

# Modern TLS versions accepted by the 912 Controls minimum. Callers can
# override, but this is the safe default for ``tls_configured``.
DEFAULT_PROTOCOLS = ("TLSv1.2", "TLSv1.3")


# ---------------------------------------------------------------------------
# HTTP helpers (mgmt plane on :5480 uses HTTP basic + local ``root`` cred).
# ---------------------------------------------------------------------------


def _mgmt_config(opts, profile=None):
    """Extract mgmt-plane connection config, defaulting to the tenant host."""
    pillar = opts.get("pillar", {})
    root = pillar.get("saltext.vcf", {}) or opts.get("saltext.vcf", {})
    tenant = root.get("vcfa", {})
    cfg = tenant.get("appliance") or {}
    if profile:
        prof = root.get("profiles", {}).get(profile, {}).get("vcfa", {})
        cfg = prof.get("appliance", cfg)
        tenant = prof or tenant
    # Fall back to the tenant-plane values so callers only need to
    # specify the appliance-specific overrides (mgmt user + password).
    return {
        "host": cfg.get("host") or tenant.get("host") or tenant.get("hostname"),
        "port": int(cfg.get("port", DEFAULT_MGMT_PORT)),
        "username": cfg.get("username") or "root",
        "password": cfg.get("password") or tenant.get("password"),
        "verify_ssl": cfg.get("verify_ssl", tenant.get("verify_ssl", True)),
        "timeout": cfg.get("timeout", tenant.get("timeout", vcfa.DEFAULT_TIMEOUT)),
    }


def _url(cfg, path):
    return f"https://{cfg['host']}:{cfg['port']}{path}"


def _request(method, opts, path, *, profile=None, **kwargs):
    """Perform a mgmt-plane request with basic auth + optional TLS skip."""
    cfg = _mgmt_config(opts, profile=profile)
    if not cfg["verify_ssl"]:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    resp = requests.request(
        method,
        _url(cfg, path),
        auth=(cfg["username"], cfg["password"]),
        verify=cfg["verify_ssl"],
        timeout=kwargs.pop("timeout", cfg["timeout"]),
        **kwargs,
    )
    resp.raise_for_status()
    return resp


def _get(opts, path, profile=None):
    resp = _request("GET", opts, path, profile=profile)
    if resp.content:
        return resp.json()
    return {}


def _put(opts, path, body, profile=None):
    resp = _request("PUT", opts, path, json=body, profile=profile)
    if resp.content:
        return resp.json()
    return {}


def _patch(opts, path, body, profile=None):
    resp = _request("PATCH", opts, path, json=body, profile=profile)
    if resp.content:
        return resp.json()
    return {}


# ---------------------------------------------------------------------------
# TLS profile
# ---------------------------------------------------------------------------


def tls_get(opts, profile=None):
    """Return the current appliance TLS configuration.

    Shape (documented):
    ``{"protocols": ["TLSv1.2", "TLSv1.3"], "cipherSuites": [...]}``.
    """
    return _get(opts, _TLS_PATH, profile=profile)


def tls_set(opts, protocols=None, cipher_suites=None, profile=None):
    """PUT a new TLS profile.

    ``protocols`` defaults to :data:`DEFAULT_PROTOCOLS` (TLS 1.2 + 1.3),
    matching the 912 Controls minimum. Fields not provided by the
    caller are preserved from the current config so the endpoint's
    PUT-style semantics don't clobber operator-set cipher suites.
    """
    current = tls_get(opts, profile=profile) or {}
    body = dict(current)
    body["protocols"] = list(protocols) if protocols is not None else list(DEFAULT_PROTOCOLS)
    if cipher_suites is not None:
        body["cipherSuites"] = list(cipher_suites)
    return _put(opts, _TLS_PATH, body, profile=profile)


# ---------------------------------------------------------------------------
# Services / unused-port firewall
# ---------------------------------------------------------------------------


def services_list(opts, profile=None):
    """List appliance services and their ``enabled`` flags.

    Return shape: ``[{"name": "...", "enabled": bool, "port": int, ...}, ...]``.
    Both ``content``-wrapped and bare-list responses are accepted.
    """
    resp = _get(opts, _SERVICES_PATH, profile=profile)
    if isinstance(resp, list):
        return resp
    return resp.get("content") or resp.get("items") or resp.get("services") or []


def service_get(opts, service, profile=None):
    """Return one service record, or ``None`` if not present."""
    for svc in services_list(opts, profile=profile):
        if svc.get("name") == service or svc.get("id") == service:
            return svc
    return None


def service_set_enabled(opts, service, enabled, profile=None):
    """Toggle a service's ``enabled`` flag via ``PATCH /services/{name}``.

    Returns the updated service record.
    """
    return _patch(
        opts,
        f"{_SERVICES_PATH}/{service}",
        {"enabled": bool(enabled)},
        profile=profile,
    )


def service_disable(opts, service, profile=None):
    """Disable *service*. Idempotent — no request if already disabled."""
    svc = service_get(opts, service, profile=profile)
    if svc is None:
        raise ValueError(f"unknown appliance service: {service!r}")
    if not svc.get("enabled", False):
        return svc
    return service_set_enabled(opts, service, False, profile=profile)


def service_enable(opts, service, profile=None):
    """Enable *service*. Idempotent — no request if already enabled."""
    svc = service_get(opts, service, profile=profile)
    if svc is None:
        raise ValueError(f"unknown appliance service: {service!r}")
    if svc.get("enabled", False):
        return svc
    return service_set_enabled(opts, service, True, profile=profile)


def firewall_list(opts, profile=None):
    """Return the appliance port allow-list.

    Shape: ``[{"port": int, "protocol": "tcp"|"udp", "allowed": bool, ...}, ...]``.
    """
    resp = _get(opts, _FIREWALL_PATH, profile=profile)
    if isinstance(resp, list):
        return resp
    return resp.get("content") or resp.get("items") or resp.get("rules") or []


# ---------------------------------------------------------------------------
# SSH
# ---------------------------------------------------------------------------


def ssh_get(opts, profile=None):
    """Return current SSH daemon config.

    Shape: ``{"enabled": bool, "rootLogin": bool, "adminLogin": bool}``.
    """
    return _get(opts, _SSH_PATH, profile=profile)


def ssh_set(opts, enabled=None, root_enabled=None, admin_enabled=None, profile=None):
    """Update the SSH daemon config.

    Only fields explicitly supplied by the caller are sent; unset
    parameters are preserved from the current configuration.
    """
    current = ssh_get(opts, profile=profile) or {}
    body = dict(current)
    if enabled is not None:
        body["enabled"] = bool(enabled)
    if root_enabled is not None:
        body["rootLogin"] = bool(root_enabled)
    if admin_enabled is not None:
        body["adminLogin"] = bool(admin_enabled)
    return _put(opts, _SSH_PATH, body, profile=profile)


def get_or_none(opts, fetch, profile=None):
    """Utility: return ``fetch(opts, profile=profile)`` or ``None`` on 404."""
    try:
        return fetch(opts, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise
