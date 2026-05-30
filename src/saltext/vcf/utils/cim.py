"""
ESXi CIM/WBEM connection helpers (pywbem).

ESXi hosts expose hardware health (fans, PSUs, RAID controllers, sensors)
via a CIM/WBEM endpoint on port 5989 (HTTPS) or 5988 (HTTP). This is the
only programmatic path for out-of-band hardware health — the vSphere API
does not expose this data.

Config is read from Salt opts/pillar under ``saltext.vcf.esxi`` — same
pillar block as the standalone ESXi REST modules::

    saltext.vcf:
      esxi:
        host: esxi01.example.com
        username: root
        password: secret
        verify_ssl: false
        cim_port: 5989       # optional; default 5989
"""

import logging

import pywbem

from saltext.vcf.utils import esxi as esxi_rest

log = logging.getLogger(__name__)

# Cached WBEMConnection per (host, username). pywbem connections are cheap
# but reusing them avoids per-call SSL handshakes.
_CONN_CACHE: dict[str, pywbem.WBEMConnection] = {}


def get_config(opts, profile=None):
    """CIM shares the ESXi pillar block. Adds a ``cim_port`` field."""
    cfg = esxi_rest.get_config(opts, profile=profile)
    pillar = opts.get("pillar", {})
    root = pillar.get("saltext.vcf", {}) or opts.get("saltext.vcf", {})
    esxi_cfg = root.get("esxi", {})
    if profile:
        esxi_cfg = root.get("profiles", {}).get(profile, {}).get("esxi", esxi_cfg)
    cfg["cim_port"] = esxi_cfg.get("cim_port", 5989)
    return cfg


def get_connection(opts, profile=None):
    """Return a connected :class:`pywbem.WBEMConnection`.

    Cached per ``(host, username)``. The connection talks to the ESXi host's
    SFCB CIM provider at ``https://host:5989``.
    """
    cfg = get_config(opts, profile=profile)
    host = cfg["host"]
    username = cfg["username"]
    cache_key = f"{host}:{username}"

    if cache_key in _CONN_CACHE:
        return _CONN_CACHE[cache_key]

    url = f"https://{host}:{cfg['cim_port']}"
    conn = pywbem.WBEMConnection(
        url,
        (username, cfg["password"]),
        default_namespace="root/cimv2",
        no_verification=not cfg["verify_ssl"],
    )
    _CONN_CACHE[cache_key] = conn
    return conn


def invalidate_connection(opts, profile=None):
    cfg = get_config(opts, profile=profile)
    _CONN_CACHE.pop(f"{cfg['host']}:{cfg['username']}", None)
