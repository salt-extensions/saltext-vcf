"""
VCF Operations (suite-api) REST connection helpers.

VCF Operations exposes a token-authenticated REST API at
``/suite-api/api/...``. A token is acquired with::

    POST /suite-api/api/auth/token/acquire
    { "username": "...", "password": "...", "authSource": "LOCAL" }

The response field is literally ``token`` (not ``accessToken``). Subsequent
requests use ``Authorization: vRealizeOpsToken <token>``.

Config is read from Salt opts/pillar under ``saltext.vcf.vcf_ops``::

    saltext.vcf:
      vcf_ops:
        host: ops.vcf.nimbus.internal
        username: admin
        password: VMware123!
        auth_source: LOCAL          # optional; default LOCAL
        verify_ssl: false
"""

import logging

import requests
import urllib3

log = logging.getLogger(__name__)

_TOKEN_CACHE: dict[str, str] = {}


def get_config(opts, profile=None):
    """Extract VCF Operations connection config."""
    pillar = opts.get("pillar", {})
    root = pillar.get("saltext.vcf", {}) or opts.get("saltext.vcf", {})
    cfg = root.get("vcf_ops", {})
    if profile:
        cfg = root.get("profiles", {}).get(profile, {}).get("vcf_ops", cfg)
    return {
        "host": cfg.get("host") or cfg.get("hostname"),
        "username": cfg.get("username") or cfg.get("user"),
        "password": cfg.get("password"),
        "auth_source": cfg.get("auth_source", "LOCAL"),
        "verify_ssl": cfg.get("verify_ssl", True),
    }


def get_token(opts, profile=None):
    """Acquire and cache a VCF Operations auth token. Returns the raw token string."""
    cfg = get_config(opts, profile=profile)
    host = cfg["host"]
    username = cfg["username"]
    verify = cfg["verify_ssl"]
    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    cache_key = f"{host}:{username}"
    if cache_key in _TOKEN_CACHE:
        return _TOKEN_CACHE[cache_key]

    resp = requests.post(
        f"https://{host}/suite-api/api/auth/token/acquire",
        json={
            "username": username,
            "password": cfg["password"],
            "authSource": cfg["auth_source"],
        },
        verify=verify,
        timeout=30,
    )
    resp.raise_for_status()
    token = resp.json()["token"]
    _TOKEN_CACHE[cache_key] = token
    return token


def invalidate_token(opts, profile=None):
    cfg = get_config(opts, profile=profile)
    _TOKEN_CACHE.pop(f"{cfg['host']}:{cfg['username']}", None)


def _session(opts, profile=None):
    cfg = get_config(opts, profile=profile)
    verify = cfg["verify_ssl"]
    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    token = get_token(opts, profile=profile)
    session = requests.Session()
    session.verify = verify
    session.headers.update(
        {
            "Authorization": f"vRealizeOpsToken {token}",
            "Accept": "application/json",
        }
    )
    return session, cfg["host"]


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


def api_delete(opts, path, params=None, profile=None):
    session, host = _session(opts, profile=profile)
    resp = session.delete(f"https://{host}{path}", params=params, timeout=30)
    resp.raise_for_status()
    return {}
