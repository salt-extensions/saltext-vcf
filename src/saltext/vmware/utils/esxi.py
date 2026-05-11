"""
ESXi host REST API connection helpers — **standalone/unmanaged ESXi only**.

ESXi exposes the vAPI session endpoint at ``POST /api/session`` on each host.
On hosts that have been joined to a vCenter, that endpoint is blocked
(``400`` on real VCF 9.2). For hosts managed by vCenter, configuration is
done at the cluster level via the Configuration Profile API; see
:mod:`saltext.vmware.clients.cluster_config`.

Config is read from Salt opts/pillar under ``saltext.vmware.esxi``::

    saltext.vmware:
      esxi:
        host: esxi-test.example.com
        username: root
        password: VMware123!
        verify_ssl: false
"""

import logging

import requests
import urllib3

log = logging.getLogger(__name__)

_SESSION_CACHE: dict[str, str] = {}


def get_config(opts, profile=None):
    """Extract ESXi connection config from Salt opts/pillar."""
    pillar = opts.get("pillar", {})
    root = pillar.get("saltext.vmware", {}) or opts.get("saltext.vmware", {})
    cfg = root.get("esxi", {})
    if profile:
        cfg = root.get("profiles", {}).get(profile, {}).get("esxi", cfg)
    return {
        "host": cfg.get("host") or cfg.get("hostname"),
        "username": cfg.get("username") or cfg.get("user"),
        "password": cfg.get("password"),
        "verify_ssl": cfg.get("verify_ssl", True),
    }


def get_session(opts, profile=None):
    """Return ``(session, host)`` authenticated against the ESXi host."""
    cfg = get_config(opts, profile=profile)
    host = cfg["host"]
    verify = cfg["verify_ssl"]
    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    cache_key = f"{host}:{cfg['username']}"
    if cache_key not in _SESSION_CACHE:
        resp = requests.post(
            f"https://{host}/api/session",
            auth=(cfg["username"], cfg["password"]),
            verify=verify,
            timeout=30,
        )
        resp.raise_for_status()
        _SESSION_CACHE[cache_key] = resp.json()

    session = requests.Session()
    session.verify = verify
    session.headers.update({"vmware-api-session-id": _SESSION_CACHE[cache_key]})
    return session, host


def invalidate_session(opts, profile=None):
    cfg = get_config(opts, profile=profile)
    _SESSION_CACHE.pop(f"{cfg['host']}:{cfg['username']}", None)


def _session(opts, profile=None):
    return get_session(opts, profile=profile)


def api_get(opts, path, params=None, profile=None):
    session, host = _session(opts, profile=profile)
    resp = session.get(f"https://{host}{path}", params=params, timeout=30)
    resp.raise_for_status()
    if resp.content:
        return resp.json()
    return {}


def api_post(opts, path, body=None, params=None, profile=None):
    session, host = _session(opts, profile=profile)
    resp = session.post(f"https://{host}{path}", json=body, params=params, timeout=30)
    resp.raise_for_status()
    if resp.content:
        return resp.json()
    return {}


def api_patch(opts, path, body=None, profile=None):
    session, host = _session(opts, profile=profile)
    resp = session.patch(f"https://{host}{path}", json=body, timeout=30)
    resp.raise_for_status()
    if resp.content:
        return resp.json()
    return {}


def api_delete(opts, path, profile=None):
    session, host = _session(opts, profile=profile)
    resp = session.delete(f"https://{host}{path}", timeout=30)
    resp.raise_for_status()
    return {}
