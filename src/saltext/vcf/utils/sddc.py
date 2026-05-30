"""
SDDC Manager REST API connection helpers.

Authentication uses Bearer JWT tokens from ``POST /v1/tokens``. The token is
cached per (host, username) pair for the lifetime of the Salt loader session.

Config is read from Salt opts/pillar under ``saltext.vcf.sddc_manager``:

.. code-block:: yaml

    saltext.vcf:
      sddc_manager:
        host: sddc-manager.example.test
        username: administrator@vsphere.local
        password: secret
        verify_ssl: false
"""

import logging

import requests
import urllib3

log = logging.getLogger(__name__)

_TOKEN_CACHE: dict[str, str] = {}


def get_config(opts, profile=None):
    """
    Extract SDDC Manager connection config from Salt opts/pillar.

    Returns a dict with keys: host, username, password, verify_ssl.
    """
    pillar = opts.get("pillar", {})
    root = pillar.get("saltext.vcf", {}) or opts.get("saltext.vcf", {})
    cfg = root.get("sddc_manager", {})
    if profile:
        cfg = root.get("profiles", {}).get(profile, {}).get("sddc_manager", cfg)
    return {
        "host": cfg.get("host") or cfg.get("hostname"),
        "username": cfg.get("username") or cfg.get("user"),
        "password": cfg.get("password"),
        "verify_ssl": cfg.get("verify_ssl", True),
    }


def get_token(opts, profile=None):
    """
    Acquire and cache a Bearer JWT from SDDC Manager.

    Returns the raw token string (without the ``Bearer`` prefix).
    """
    cfg = get_config(opts, profile=profile)
    host = cfg["host"]
    username = cfg["username"]
    password = cfg["password"]
    verify = cfg["verify_ssl"]

    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    cache_key = f"{host}:{username}"
    if cache_key in _TOKEN_CACHE:
        return _TOKEN_CACHE[cache_key]

    url = f"https://{host}/v1/tokens"
    resp = requests.post(
        url,
        json={"username": username, "password": password},
        verify=verify,
        timeout=30,
    )
    resp.raise_for_status()
    token = resp.json()["accessToken"]
    _TOKEN_CACHE[cache_key] = token
    return token


def invalidate_token(opts, profile=None):
    """Remove the cached token, forcing re-authentication on next call."""
    cfg = get_config(opts, profile=profile)
    cache_key = f"{cfg['host']}:{cfg['username']}"
    _TOKEN_CACHE.pop(cache_key, None)


def _session(opts, profile=None):
    cfg = get_config(opts, profile=profile)
    verify = cfg["verify_ssl"]
    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    token = get_token(opts, profile=profile)
    session = requests.Session()
    session.verify = verify
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session, cfg["host"]


def api_get(opts, path, params=None, profile=None):
    """GET ``/v1/<path>`` from SDDC Manager and return parsed JSON."""
    session, host = _session(opts, profile=profile)
    url = f"https://{host}{path}"
    resp = session.get(url, params=params, timeout=30)
    resp.raise_for_status()
    if resp.content:
        return resp.json()
    return {}


def api_post(opts, path, body=None, profile=None):
    """POST JSON *body* to SDDC Manager and return parsed JSON."""
    session, host = _session(opts, profile=profile)
    url = f"https://{host}{path}"
    resp = session.post(url, json=body, timeout=30)
    resp.raise_for_status()
    if resp.content:
        return resp.json()
    return {}


def api_patch(opts, path, body=None, profile=None):
    """PATCH JSON *body* to SDDC Manager and return parsed JSON."""
    session, host = _session(opts, profile=profile)
    url = f"https://{host}{path}"
    resp = session.patch(url, json=body, timeout=30)
    resp.raise_for_status()
    if resp.content:
        return resp.json()
    return {}


def api_put(opts, path, body=None, profile=None):
    """PUT JSON *body* to SDDC Manager and return parsed JSON."""
    session, host = _session(opts, profile=profile)
    url = f"https://{host}{path}"
    resp = session.put(url, json=body, timeout=30)
    resp.raise_for_status()
    if resp.content:
        return resp.json()
    return {}


def api_delete(opts, path, profile=None):
    """DELETE a resource from SDDC Manager."""
    session, host = _session(opts, profile=profile)
    url = f"https://{host}{path}"
    resp = session.delete(url, timeout=30)
    resp.raise_for_status()
    return {}
