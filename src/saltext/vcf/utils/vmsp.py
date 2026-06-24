"""
VMSP (VCF Security Platform) REST API connection helpers.

Authentication uses the VMSP identity token endpoint
(``POST /api/v1/identity/token`` with ``grant_type=password``), which returns an
``access_token`` used as a Bearer token on subsequent calls. The token is cached
per ``(host, username)`` pair for the lifetime of the Salt loader process.

Configuration is read from Salt opts/pillar under ``saltext.vcf.vmsp``:

.. code-block:: yaml

    saltext.vcf:
      vmsp:
        host: vsp-platform.example.test
        username: admin@vsp.local
        password: secret
        verify_ssl: false
        # Optional. Default 60s.
        timeout: 60

The configuration controls (NTP, DNS, syslog) are expressed against the ``vsp``
component object returned by ``GET /api/v1/components``. Reading the full
configuration requires the ``x-vmsp-return-all-configuration: true`` header.
"""

import logging
import time

import requests
import urllib3

log = logging.getLogger(__name__)

_TOKEN_CACHE: dict[str, str] = {}

DEFAULT_TIMEOUT = 60

# VMSP API paths
TOKEN_PATH = "/api/v1/identity/token"
COMPONENTS_PATH = "/api/v1/components"
COMPONENT_APPLY_PATH = "/api/v1/components/{}?action=apply"
TASK_PATH = "/api/v1/tasks/{}"

# Name of the platform component that holds the NTP/DNS/syslog configuration.
VSP_COMPONENT_NAME = "vsp"

# Task polling
TASK_TERMINAL = ("Succeeded", "Failed")
TASK_POLL_INTERVAL = 15
TASK_TIMEOUT = 900


def get_config(opts, profile=None):
    """
    Extract VMSP connection config from Salt opts/pillar.

    Returns a dict with keys: host, username, password, verify_ssl, timeout.
    """
    pillar = opts.get("pillar", {})
    root = pillar.get("saltext.vcf", {}) or opts.get("saltext.vcf", {})
    cfg = root.get("vmsp", {})
    if profile:
        cfg = root.get("profiles", {}).get(profile, {}).get("vmsp", cfg)
    return {
        "host": cfg.get("host") or cfg.get("hostname"),
        "username": cfg.get("username") or cfg.get("user"),
        "password": cfg.get("password"),
        "verify_ssl": cfg.get("verify_ssl", True),
        "timeout": cfg.get("timeout", DEFAULT_TIMEOUT),
    }


def _raise_for_status(resp):
    """Raise ``requests.HTTPError`` that includes the VMSP response body."""
    if resp.status_code < 400:
        return
    try:
        detail = resp.text
    except Exception:  # pragma: no cover - defensive
        detail = "<unreadable response body>"
    method = resp.request.method if resp.request is not None else "?"
    raise requests.HTTPError(
        f"{resp.status_code} {resp.reason} for {method} {resp.url}: {detail}",
        response=resp,
    )


def _get_token(cfg):
    """Authenticate against the VMSP identity endpoint and return an access token."""
    host = cfg["host"]
    username = cfg["username"]
    password = cfg["password"]
    verify = cfg["verify_ssl"]

    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    cache_key = f"{host}:{username}"
    if cache_key not in _TOKEN_CACHE:
        url = f"https://{host}{TOKEN_PATH}"
        resp = requests.post(
            url,
            data={
                "grant_type": "password",
                "username": username,
                "password": password,
            },
            headers={"content-type": "application/x-www-form-urlencoded"},
            verify=verify,
            timeout=cfg["timeout"],
        )
        _raise_for_status(resp)
        token = resp.json().get("access_token")
        if not token:
            raise requests.HTTPError(f"No access_token in VMSP token response from {url}")
        _TOKEN_CACHE[cache_key] = token
    return _TOKEN_CACHE[cache_key]


def invalidate_token(opts, profile=None):
    """Remove the cached token, forcing re-authentication on next call."""
    cfg = get_config(opts, profile=profile)
    _TOKEN_CACHE.pop(f"{cfg['host']}:{cfg['username']}", None)


def get_session(opts, profile=None):
    """Return an authenticated ``(requests.Session, host)`` tuple for VMSP."""
    cfg = get_config(opts, profile=profile)
    token = _get_token(cfg)
    session = requests.Session()
    session.verify = cfg["verify_ssl"]
    session.headers.update(
        {
            "authorization": f"Bearer {token}",
            "content-type": "application/json",
        }
    )
    return session, cfg["host"]


def _timeout(opts, profile):
    return get_config(opts, profile=profile)["timeout"]


def api_get(opts, path, params=None, headers=None, profile=None):
    """GET ``<path>`` from VMSP and return parsed JSON."""
    session, host = get_session(opts, profile=profile)
    url = f"https://{host}{path}"
    resp = session.get(url, params=params, headers=headers, timeout=_timeout(opts, profile))
    _raise_for_status(resp)
    if resp.content:
        return resp.json()
    return {}


def api_post(opts, path, body=None, params=None, profile=None):
    """POST JSON *body* to VMSP and return parsed JSON."""
    session, host = get_session(opts, profile=profile)
    url = f"https://{host}{path}"
    resp = session.post(url, json=body, params=params, timeout=_timeout(opts, profile))
    _raise_for_status(resp)
    if resp.content:
        return resp.json()
    return {}


def get_component(opts, name=VSP_COMPONENT_NAME, profile=None):
    """Return the full component dict for *name* (default ``vsp``), or ``None``.

    The ``x-vmsp-return-all-configuration`` header is required for the response
    to include the nested ``spec.configuration`` the controls read from.
    """
    resp = api_get(
        opts,
        COMPONENTS_PATH,
        headers={"x-vmsp-return-all-configuration": "true"},
        profile=profile,
    )
    components = resp.get("components", []) if isinstance(resp, dict) else resp
    for component in components or []:
        if component.get("name") == name:
            return component
    return None


def apply_component(opts, component_id, payload, profile=None):
    """Apply a configuration *payload* to a component; return the task id."""
    resp = api_post(opts, COMPONENT_APPLY_PATH.format(component_id), body=payload, profile=profile)
    task_id = resp.get("id") if isinstance(resp, dict) else None
    if not task_id:
        raise requests.HTTPError(f"No task id returned from apply on component {component_id}: {resp}")
    return task_id


def wait_for_task(opts, task_id, profile=None, timeout=TASK_TIMEOUT, interval=TASK_POLL_INTERVAL):
    """Poll a VMSP task until it reaches a terminal phase. Raise on failure/timeout."""
    deadline = timeout
    elapsed = 0
    while elapsed <= deadline:
        info = api_get(opts, TASK_PATH.format(task_id), profile=profile)
        phase = info.get("phase", "")
        status = info.get("status", "")
        if phase in TASK_TERMINAL:
            if phase == "Succeeded" and status == "Succeeded":
                return info
            raise requests.HTTPError(f"VMSP task {task_id} failed (phase={phase}, status={status})")
        time.sleep(interval)
        elapsed += interval
    raise TimeoutError(f"VMSP task {task_id} did not complete within {timeout}s")
