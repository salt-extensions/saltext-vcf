"""
VCF Installer REST API connection helpers.

The VCF Installer (formerly Cloud Builder) is the Day-0 bringup appliance that
deploys management-domain ESXi, vCenter, NSX, the VMSP cluster, and SDDC
Manager. It exposes a REST API at ``https://<installer>/v1/`` authenticated
with HTTP Basic. No token endpoint — credentials are sent on every request,
so a ``requests.Session`` with ``auth=`` is enough.

Config is read from Salt opts/pillar under ``saltext.vmware.vcf_installer``::

    saltext.vmware:
      vcf_installer:
        host: installer.vcf.nimbus.internal
        username: admin
        password: VMware123!VMware123!
        verify_ssl: false
"""

import logging

import requests
import urllib3

log = logging.getLogger(__name__)

# Sessions are cheap (basic auth, no token), but cache per (host, username)
# to match the other utils' invalidate() semantics.
_SESSION_CACHE: dict[str, requests.Session] = {}


def get_config(opts, profile=None):
    """Extract VCF Installer connection config from Salt opts/pillar."""
    pillar = opts.get("pillar", {})
    root = pillar.get("saltext.vmware", {}) or opts.get("saltext.vmware", {})
    cfg = root.get("vcf_installer", {})
    if profile:
        cfg = root.get("profiles", {}).get(profile, {}).get("vcf_installer", cfg)
    return {
        "host": cfg.get("host") or cfg.get("hostname"),
        "username": cfg.get("username") or cfg.get("user", "admin"),
        "password": cfg.get("password"),
        "verify_ssl": cfg.get("verify_ssl", True),
    }


def _session(opts, profile=None):
    cfg = get_config(opts, profile=profile)
    host = cfg["host"]
    username = cfg["username"]
    verify = cfg["verify_ssl"]
    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    cache_key = f"{host}:{username}"
    if cache_key not in _SESSION_CACHE:
        session = requests.Session()
        session.auth = (username, cfg["password"])
        session.verify = verify
        _SESSION_CACHE[cache_key] = session
    return _SESSION_CACHE[cache_key], host


def invalidate_session(opts, profile=None):
    """Drop the cached session for the configured target."""
    cfg = get_config(opts, profile=profile)
    cache_key = f"{cfg['host']}:{cfg['username']}"
    _SESSION_CACHE.pop(cache_key, None)


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


def api_put(opts, path, body=None, profile=None):
    session, host = _session(opts, profile=profile)
    resp = session.put(f"https://{host}{path}", json=body, timeout=30)
    resp.raise_for_status()
    if resp.content:
        return resp.json()
    return {}


def api_delete(opts, path, profile=None):
    session, host = _session(opts, profile=profile)
    resp = session.delete(f"https://{host}{path}", timeout=30)
    resp.raise_for_status()
    return {}
