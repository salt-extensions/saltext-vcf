"""
vCenter REST API connection helpers.

Authentication uses the vCenter session API (``POST /api/session``), which returns
a ``vmware-api-session-id`` token. The token is cached per (host, username) pair
in a module-level dict so that multiple calls within the same Salt loader session
do not re-authenticate on every invocation.

Config is read from Salt opts/pillar under ``saltext.vcf.vcenter``:

.. code-block:: yaml

    saltext.vcf:
      vcenter:
        host: mgmt-vc.vcf.nimbus.internal
        username: administrator@vsphere.local
        password: VMware123!VMware123!
        verify_ssl: false
        # Optional. Default 30s; bump for long-running calls like OVF deploy.
        timeout: 1800
"""

import logging

import requests
import urllib3

log = logging.getLogger(__name__)

_SESSION_CACHE: dict[str, str] = {}

# Default per-request timeout (seconds). Override per-call by passing
# ``timeout=`` to any ``api_*`` helper, or globally via the
# ``saltext.vcf.vcenter.timeout`` pillar key.
DEFAULT_TIMEOUT = 30


def get_config(opts, profile=None):
    """
    Extract vCenter connection config from Salt opts/pillar.

    Returns a dict with keys: host, username, password, verify_ssl, timeout.
    """
    pillar = opts.get("pillar", {})
    root = pillar.get("saltext.vcf", {}) or opts.get("saltext.vcf", {})
    cfg = root.get("vcenter", {})
    if profile:
        cfg = root.get("profiles", {}).get(profile, {}).get("vcenter", cfg)
    return {
        "host": cfg.get("host") or cfg.get("hostname"),
        "username": cfg.get("username") or cfg.get("user"),
        "password": cfg.get("password"),
        "verify_ssl": cfg.get("verify_ssl", True),
        "timeout": cfg.get("timeout", DEFAULT_TIMEOUT),
    }


def _resolve_timeout(opts, profile, override):
    """Return the effective request timeout: per-call > pillar > module default."""
    if override is not None:
        return override
    return get_config(opts, profile=profile)["timeout"]


def get_session(opts, profile=None):
    """
    Return an authenticated ``(requests.Session, host)`` tuple for vCenter.

    The session has the ``vmware-api-session-id`` header pre-set. The token is
    cached for the lifetime of the Python process; call :func:`invalidate_session`
    to force re-authentication.
    """
    cfg = get_config(opts, profile=profile)
    host = cfg["host"]
    username = cfg["username"]
    password = cfg["password"]
    verify = cfg["verify_ssl"]

    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    cache_key = f"{host}:{username}"
    if cache_key not in _SESSION_CACHE:
        url = f"https://{host}/api/session"
        resp = requests.post(url, auth=(username, password), verify=verify, timeout=cfg["timeout"])
        resp.raise_for_status()
        _SESSION_CACHE[cache_key] = resp.json()

    session = requests.Session()
    session.verify = verify
    session.headers.update({"vmware-api-session-id": _SESSION_CACHE[cache_key]})
    return session, host


def invalidate_session(opts, profile=None):
    """Remove the cached session token, forcing re-authentication on next call."""
    cfg = get_config(opts, profile=profile)
    cache_key = f"{cfg['host']}:{cfg['username']}"
    _SESSION_CACHE.pop(cache_key, None)


def _session(opts, profile=None):
    return get_session(opts, profile=profile)


def api_get(opts, path, params=None, profile=None, timeout=None):
    """GET ``/api/<path>`` from vCenter and return parsed JSON.

    *timeout* overrides the per-request timeout in seconds. Defaults to the
    pillar ``saltext.vcf.vcenter.timeout`` value, or :data:`DEFAULT_TIMEOUT`.
    """
    session, host = _session(opts, profile=profile)
    url = f"https://{host}{path}"
    resp = session.get(url, params=params, timeout=_resolve_timeout(opts, profile, timeout))
    resp.raise_for_status()
    if resp.content:
        return resp.json()
    return {}


def api_post(opts, path, body=None, params=None, profile=None, timeout=None):
    """POST JSON *body* to vCenter and return parsed JSON.

    *timeout* overrides the per-request timeout (seconds). Long-running calls
    like OVF deploy should pass an explicit higher value.
    """
    session, host = _session(opts, profile=profile)
    url = f"https://{host}{path}"
    resp = session.post(
        url, json=body, params=params, timeout=_resolve_timeout(opts, profile, timeout)
    )
    resp.raise_for_status()
    if resp.content:
        return resp.json()
    return {}


def api_patch(opts, path, body=None, profile=None, timeout=None):
    """PATCH JSON *body* to vCenter and return parsed JSON."""
    session, host = _session(opts, profile=profile)
    url = f"https://{host}{path}"
    resp = session.patch(url, json=body, timeout=_resolve_timeout(opts, profile, timeout))
    resp.raise_for_status()
    if resp.content:
        return resp.json()
    return {}


def api_put(opts, path, body=None, profile=None, timeout=None):
    """PUT JSON *body* to vCenter and return parsed JSON."""
    session, host = _session(opts, profile=profile)
    url = f"https://{host}{path}"
    resp = session.put(url, json=body, timeout=_resolve_timeout(opts, profile, timeout))
    resp.raise_for_status()
    if resp.content:
        return resp.json()
    return {}


def api_delete(opts, path, profile=None, timeout=None):
    """DELETE a resource from vCenter."""
    session, host = _session(opts, profile=profile)
    url = f"https://{host}{path}"
    resp = session.delete(url, timeout=_resolve_timeout(opts, profile, timeout))
    resp.raise_for_status()
    return {}
