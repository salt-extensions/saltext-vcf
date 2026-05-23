"""
VCF Automation (VCFA / Aria Automation) REST connection helpers.

VCF Automation 9.x uses the two-step CSP token flow inherited from
vRA 8.x / Aria Automation:

.. code-block::

    POST /csp/gateway/am/api/login                # refresh-token acquire
         {"username": "...", "password": "...", "domain": "System Domain"}
      -> {"refresh_token": "..."}

    POST /iaas/api/login                          # bearer exchange
         {"refreshToken": "..."}
      -> {"token": "<bearer>"}

The refresh token is the long-lived identity; the bearer expires
~every 8h. Both are cached per ``(host, username)``; if a request
returns 401 the bearer is re-minted from the cached refresh token.

Config is read from Salt opts/pillar under ``saltext.vcf.vcfa``::

    saltext.vcf:
      vcfa:
        host: automation.vcf.example.com
        username: configadmin
        password: VMware123!
        domain: System Domain       # optional; default "System Domain"
        verify_ssl: false
        timeout: 60                 # optional; default DEFAULT_TIMEOUT

VCFA spans several microservices (``/iaas/api``, ``/catalog/api``,
``/abx/api``, ``/vco/api``, ``/policy/api``, ``/blueprint/api``,
``/event-broker/api``, ``/form-service/api``, plus the CSP gateway
itself). They all share the same bearer token; this module's
``api_*`` helpers don't prepend a base path so callers pass the full
``/<service>/api/...`` path.
"""

import logging
import time

import requests
import urllib3

log = logging.getLogger(__name__)

# (refresh_token, bearer) tuples cached per (host, username).
_TOKEN_CACHE: dict[str, tuple[str, str]] = {}

DEFAULT_TIMEOUT = 30
DEFAULT_DOMAIN = "System Domain"


def get_config(opts, profile=None):
    """Extract VCF Automation connection config from Salt opts/pillar."""
    pillar = opts.get("pillar", {})
    root = pillar.get("saltext.vcf", {}) or opts.get("saltext.vcf", {})
    cfg = root.get("vcfa", {})
    if profile:
        cfg = root.get("profiles", {}).get(profile, {}).get("vcfa", cfg)
    return {
        "host": cfg.get("host") or cfg.get("hostname"),
        "username": cfg.get("username") or cfg.get("user"),
        "password": cfg.get("password"),
        "domain": cfg.get("domain", DEFAULT_DOMAIN),
        "verify_ssl": cfg.get("verify_ssl", True),
        "timeout": cfg.get("timeout", DEFAULT_TIMEOUT),
    }


def _resolve_timeout(opts, profile, override):
    if override is not None:
        return override
    return get_config(opts, profile=profile)["timeout"]


def _acquire_refresh_token(cfg):
    """POST /csp/gateway/am/api/login → refresh_token."""
    resp = requests.post(
        f"https://{cfg['host']}/csp/gateway/am/api/login",
        json={
            "username": cfg["username"],
            "password": cfg["password"],
            "domain": cfg["domain"],
        },
        verify=cfg["verify_ssl"],
        timeout=cfg["timeout"],
    )
    resp.raise_for_status()
    return resp.json()["refresh_token"]


def _exchange_for_bearer(cfg, refresh_token):
    """POST /iaas/api/login → bearer."""
    resp = requests.post(
        f"https://{cfg['host']}/iaas/api/login",
        json={"refreshToken": refresh_token},
        verify=cfg["verify_ssl"],
        timeout=cfg["timeout"],
    )
    resp.raise_for_status()
    return resp.json()["token"]


def get_tokens(opts, profile=None):
    """Return ``(refresh_token, bearer)``, acquiring + caching as needed."""
    cfg = get_config(opts, profile=profile)
    if not cfg["verify_ssl"]:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    cache_key = f"{cfg['host']}:{cfg['username']}"
    cached = _TOKEN_CACHE.get(cache_key)
    if cached is not None:
        return cached

    refresh = _acquire_refresh_token(cfg)
    bearer = _exchange_for_bearer(cfg, refresh)
    _TOKEN_CACHE[cache_key] = (refresh, bearer)
    return _TOKEN_CACHE[cache_key]


def invalidate_token(opts, profile=None):
    """Clear the cached (refresh, bearer) for this host+user."""
    cfg = get_config(opts, profile=profile)
    _TOKEN_CACHE.pop(f"{cfg['host']}:{cfg['username']}", None)


def _refresh_bearer(opts, profile=None):
    """Re-mint the bearer from the cached refresh token (used on 401)."""
    cfg = get_config(opts, profile=profile)
    cache_key = f"{cfg['host']}:{cfg['username']}"
    cached = _TOKEN_CACHE.get(cache_key)
    if cached is None:
        return get_tokens(opts, profile=profile)[1]
    refresh, _ = cached
    bearer = _exchange_for_bearer(cfg, refresh)
    _TOKEN_CACHE[cache_key] = (refresh, bearer)
    return bearer


def _session(opts, profile=None):
    cfg = get_config(opts, profile=profile)
    verify = cfg["verify_ssl"]
    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    _, bearer = get_tokens(opts, profile=profile)
    session = requests.Session()
    session.verify = verify
    session.headers.update(
        {
            "Authorization": f"Bearer {bearer}",
            "Accept": "application/json",
        }
    )
    return session, cfg["host"]


def _request(method, opts, path, *, profile=None, timeout=None, **kwargs):
    """Underlying request, re-tries once on 401 by refreshing the bearer."""
    session, host = _session(opts, profile=profile)
    url = f"https://{host}{path}"
    eff_timeout = _resolve_timeout(opts, profile, timeout)
    resp = session.request(method, url, timeout=eff_timeout, **kwargs)
    if resp.status_code == 401:
        new_bearer = _refresh_bearer(opts, profile=profile)
        session.headers["Authorization"] = f"Bearer {new_bearer}"
        resp = session.request(method, url, timeout=eff_timeout, **kwargs)
    resp.raise_for_status()
    return resp


def api_get(opts, path, params=None, profile=None, timeout=None):
    resp = _request("GET", opts, path, params=params, profile=profile, timeout=timeout)
    if resp.content:
        return resp.json()
    return {}


def api_post(opts, path, body=None, params=None, profile=None, timeout=None):
    resp = _request("POST", opts, path, json=body, params=params, profile=profile, timeout=timeout)
    if resp.content:
        return resp.json()
    return {}


def api_put(opts, path, body=None, params=None, profile=None, timeout=None):
    resp = _request("PUT", opts, path, json=body, params=params, profile=profile, timeout=timeout)
    if resp.content:
        return resp.json()
    return {}


def api_patch(opts, path, body=None, params=None, profile=None, timeout=None):
    resp = _request("PATCH", opts, path, json=body, params=params, profile=profile, timeout=timeout)
    if resp.content:
        return resp.json()
    return {}


def api_delete(opts, path, params=None, profile=None, timeout=None):
    _request("DELETE", opts, path, params=params, profile=profile, timeout=timeout)
    return {}


def api_post_multipart(opts, path, files, params=None, profile=None, timeout=None):
    """Multipart POST (vRO package import, etc.).

    *files* is the dict requests expects: ``{"file": (name, fileobj,
    content_type)}``. The JSON ``Content-Type`` header is removed; the
    bearer is preserved.
    """
    session, host = _session(opts, profile=profile)
    url = f"https://{host}{path}"
    eff_timeout = _resolve_timeout(opts, profile, timeout)
    session.headers.pop("Content-Type", None)
    resp = session.post(url, files=files, params=params, timeout=eff_timeout)
    if resp.status_code == 401:
        new_bearer = _refresh_bearer(opts, profile=profile)
        session.headers["Authorization"] = f"Bearer {new_bearer}"
        resp = session.post(url, files=files, params=params, timeout=eff_timeout)
    resp.raise_for_status()
    if resp.content:
        return resp.json()
    return {}


def wait_for_deployment(opts, deployment_id, *, timeout=1800, poll_interval=10, profile=None):
    """Poll ``/deployment/api/deployments/{id}`` until terminal.

    Returns the final deployment dict. Raises ``TimeoutError`` if not
    terminal within *timeout* seconds, or ``RuntimeError`` if the
    deployment reports a failed status. Terminal states are
    ``CREATE_SUCCESSFUL`` / ``UPDATE_SUCCESSFUL`` / ``DELETE_SUCCESSFUL``
    and the corresponding ``*_FAILED`` / ``*_INPROGRESS`` is non-terminal.
    """
    deadline = time.monotonic() + timeout
    while True:
        dep = api_get(opts, f"/deployment/api/deployments/{deployment_id}", profile=profile)
        status = dep.get("status", "")
        if status.endswith("_SUCCESSFUL"):
            return dep
        if status.endswith("_FAILED"):
            raise RuntimeError(f"deployment {deployment_id!r} failed: {status}")
        if time.monotonic() > deadline:
            raise TimeoutError(
                f"deployment {deployment_id!r} did not finish within {timeout}s (last status: {status!r})"
            )
        time.sleep(poll_interval)
