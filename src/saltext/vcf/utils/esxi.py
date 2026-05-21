"""
ESXi host connection helpers — **standalone/unmanaged ESXi only**.

All communication uses the pyVmomi SOAP/VMODL stack (``/sdk``). This works on
any ESXi host regardless of whether the vAPI endpoint (``/api/*``) is present,
which is important because shuttle-deployed test hosts omit that service.

On hosts that have been joined to a vCenter, the REST ``/api/session`` endpoint
is blocked (``400`` on real VCF 9.2). For hosts managed by vCenter, cluster-
level configuration is done via the Configuration Profile API; see
:mod:`saltext.vcf.clients.cluster_config`.

Config is read from Salt opts/pillar under ``saltext.vcf.esxi``::

    saltext.vcf:
      esxi:
        host: esxi-test.example.com
        username: root
        password: VMware123!
        verify_ssl: false
"""

import atexit
import logging
import ssl

from pyVim.connect import Disconnect
from pyVim.connect import SmartConnect

log = logging.getLogger(__name__)

# Cached ServiceInstance per cache key (avoids repeat handshakes).
_SI_CACHE: dict[str, object] = {}


def get_config(opts, profile=None):
    """Extract ESXi connection config from Salt opts/pillar."""
    pillar = opts.get("pillar", {})
    root = pillar.get("saltext.vcf", {}) or opts.get("saltext.vcf", {})
    cfg = root.get("esxi", {})
    if profile:
        cfg = root.get("profiles", {}).get(profile, {}).get("esxi", cfg)
    return {
        "host": cfg.get("host") or cfg.get("hostname"),
        "username": cfg.get("username") or cfg.get("user"),
        "password": cfg.get("password"),
        "verify_ssl": cfg.get("verify_ssl", True),
    }


def get_service_instance(opts, profile=None):
    """Return a connected pyVmomi ``ServiceInstance`` for the ESXi host.

    Cached per ``(host, port, username)``. Use
    :func:`invalidate_service_instance` to force a fresh connection.
    """
    cfg = get_config(opts, profile=profile)
    host = cfg["host"]
    port = None

    # Support ``host: esxi.example.com:8443`` or a separate ``port:`` key.
    if ":" in host:
        host, _, port_str = host.rpartition(":")
        port = int(port_str)

    cache_key = f"soap:{host}:{port or 443}:{cfg['username']}"
    if cache_key in _SI_CACHE:
        return _SI_CACHE[cache_key]

    ssl_context = None
    if not cfg["verify_ssl"]:
        ssl_context = ssl._create_unverified_context()  # noqa: SLF001

    connect_kwargs = {
        "host": host,
        "user": cfg["username"],
        "pwd": cfg["password"],
        "sslContext": ssl_context,
    }
    if port is not None:
        connect_kwargs["port"] = port

    si = SmartConnect(**connect_kwargs)
    _SI_CACHE[cache_key] = si
    atexit.register(_safe_disconnect, si)
    return si


def invalidate_service_instance(opts, profile=None):
    """Disconnect and drop the cached ServiceInstance for this host."""
    cfg = get_config(opts, profile=profile)
    host = cfg["host"]
    port = None
    if ":" in host:
        host, _, port_str = host.rpartition(":")
        port = int(port_str)
    cache_key = f"soap:{host}:{port or 443}:{cfg['username']}"
    si = _SI_CACHE.pop(cache_key, None)
    if si is not None:
        _safe_disconnect(si)


def get_host_system(opts, profile=None):
    """Return the ``vim.HostSystem`` for a standalone ESXi host.

    When connecting directly to an ESXi host (not vCenter), the SOAP tree
    contains exactly one datacenter with one host.
    """
    si = get_service_instance(opts, profile=profile)
    content = si.RetrieveContent()
    return content.rootFolder.childEntity[0].host[0]


def _safe_disconnect(si):
    try:
        Disconnect(si)
    except Exception as exc:  # pylint: disable=broad-except
        log.debug("pyVmomi ESXi disconnect raised %s; ignoring", exc)
