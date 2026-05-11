"""
NSX Policy API connection helpers.

The NSX Policy API uses HTTP Basic auth on every request. No token exchange is
performed, so there is no per-process cache — each request carries credentials.

Config is read from Salt opts/pillar under ``saltext.vmware.nsx``:

.. code-block:: yaml

    saltext.vmware:
      nsx:
        host: mgmt-nsx.vcf.nimbus.internal
        username: admin
        password: VMware123!VMware123!
        verify_ssl: false
"""

import logging

import requests
import urllib3

log = logging.getLogger(__name__)


def get_config(opts, profile=None):
    """
    Extract NSX connection config from Salt opts/pillar.

    Returns a dict with keys: host, username, password, verify_ssl.
    """
    pillar = opts.get("pillar", {})
    root = pillar.get("saltext.vmware", {}) or opts.get("saltext.vmware", {})
    cfg = root.get("nsx", {})
    if profile:
        cfg = root.get("profiles", {}).get(profile, {}).get("nsx", cfg)
    return {
        "host": cfg.get("host") or cfg.get("hostname"),
        "username": cfg.get("username") or cfg.get("user"),
        "password": cfg.get("password"),
        "verify_ssl": cfg.get("verify_ssl", True),
    }


def _session(opts, profile=None):
    cfg = get_config(opts, profile=profile)
    verify = cfg["verify_ssl"]
    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    session = requests.Session()
    session.verify = verify
    session.auth = (cfg["username"], cfg["password"])
    return session, cfg["host"]


def api_get(opts, path, params=None, profile=None):
    """GET ``/policy/api/v1/<path>`` from NSX and return parsed JSON."""
    session, host = _session(opts, profile=profile)
    url = f"https://{host}{path}"
    resp = session.get(url, params=params, timeout=30)
    resp.raise_for_status()
    if resp.content:
        return resp.json()
    return {}


def api_post(opts, path, body=None, profile=None):
    """POST JSON *body* to NSX and return parsed JSON."""
    session, host = _session(opts, profile=profile)
    url = f"https://{host}{path}"
    resp = session.post(url, json=body, timeout=30)
    resp.raise_for_status()
    if resp.content:
        return resp.json()
    return {}


def api_put(opts, path, body=None, profile=None):
    """PUT JSON *body* to NSX (create/update on Policy API) and return parsed JSON."""
    session, host = _session(opts, profile=profile)
    url = f"https://{host}{path}"
    resp = session.put(url, json=body, timeout=30)
    resp.raise_for_status()
    if resp.content:
        return resp.json()
    return {}


def api_delete(opts, path, profile=None):
    """DELETE a resource from NSX."""
    session, host = _session(opts, profile=profile)
    url = f"https://{host}{path}"
    resp = session.delete(url, timeout=30)
    resp.raise_for_status()
    return {}
