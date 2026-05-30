"""
VCF Installer REST API connection helpers.

The VCF Installer (formerly Cloud Builder) is the Day-0 bringup appliance that
deploys management-domain ESXi, vCenter, NSX, the VMSP cluster, and SDDC
Manager. It exposes a REST API at ``https://<installer>/v1/`` authenticated
with a short-lived JWT obtained from ``POST /v1/tokens``.  All subsequent
requests carry ``Authorization: Bearer <token>``; a 401 invalidates the cached
token and triggers a fresh login.

The login user is ``admin@local`` (the bare ``admin`` form is rejected with
401 even with the right password).

Config is read from Salt opts/pillar under ``saltext.vcf.vcf_installer``::

    saltext.vcf:
      vcf_installer:
        host: installer.example.test
        username: admin@local
        password: secret
        verify_ssl: false
"""

import logging

import requests
import urllib3

log = logging.getLogger(__name__)

# Sessions cache the bearer token (set on ``session.headers``) per
# (host, username), so api_get/api_post share a single login.
_SESSION_CACHE: dict[str, requests.Session] = {}


def get_config(opts, profile=None):
    """Extract VCF Installer connection config from Salt opts/pillar."""
    pillar = opts.get("pillar", {})
    root = pillar.get("saltext.vcf", {}) or opts.get("saltext.vcf", {})
    cfg = root.get("vcf_installer", {})
    if profile:
        cfg = root.get("profiles", {}).get(profile, {}).get("vcf_installer", cfg)
    return {
        "host": cfg.get("host") or cfg.get("hostname"),
        "username": cfg.get("username") or cfg.get("user", "admin@local"),
        "password": cfg.get("password"),
        "verify_ssl": cfg.get("verify_ssl", True),
    }


def _login(host, username, password, verify):
    """POST /v1/tokens and return the access token."""
    resp = requests.post(
        f"https://{host}/v1/tokens",
        json={"username": username, "password": password},
        timeout=30,
        verify=verify,
    )
    resp.raise_for_status()
    return resp.json()["accessToken"]


def _session(opts, profile=None):
    cfg = get_config(opts, profile=profile)
    host = cfg["host"]
    username = cfg["username"]
    verify = cfg["verify_ssl"]
    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    cache_key = f"{host}:{username}"
    if cache_key not in _SESSION_CACHE:
        token = _login(host, username, cfg["password"], verify)
        session = requests.Session()
        session.verify = verify
        session.headers["Authorization"] = f"Bearer {token}"
        _SESSION_CACHE[cache_key] = session
    return _SESSION_CACHE[cache_key], host


def invalidate_session(opts, profile=None):
    """Drop the cached session for the configured target."""
    cfg = get_config(opts, profile=profile)
    cache_key = f"{cfg['host']}:{cfg['username']}"
    _SESSION_CACHE.pop(cache_key, None)


def _request(method, opts, path, *, params=None, body=None, profile=None):
    """Issue an authenticated request, retrying once on 401 with a fresh token."""
    session, host = _session(opts, profile=profile)
    url = f"https://{host}{path}"
    kwargs = {"timeout": 30}
    if params is not None:
        kwargs["params"] = params
    if body is not None:
        kwargs["json"] = body
    resp = session.request(method, url, **kwargs)
    if resp.status_code == 401:
        invalidate_session(opts, profile=profile)
        session, host = _session(opts, profile=profile)
        resp = session.request(method, f"https://{host}{path}", **kwargs)
    resp.raise_for_status()
    if resp.content:
        return resp.json()
    return {}


def api_get(opts, path, params=None, profile=None):
    return _request("GET", opts, path, params=params, profile=profile)


def api_post(opts, path, body=None, params=None, profile=None):
    return _request("POST", opts, path, body=body, params=params, profile=profile)


def api_patch(opts, path, body=None, profile=None):
    return _request("PATCH", opts, path, body=body, profile=profile)


def api_put(opts, path, body=None, profile=None):
    return _request("PUT", opts, path, body=body, profile=profile)


def api_delete(opts, path, profile=None):
    return _request("DELETE", opts, path, profile=profile)
