"""
vSphere SOAP/VMODL connection helpers (pyVmomi).

Used for capabilities that vSphere REST doesn't yet expose — vSAN
imperative ops, Auto Deploy, Fault Tolerance, PerfManager historical
counters, PropertyCollector real-time subscriptions, AlarmManager
authoring, ExtensionManager, LicenseAssignmentManager, PBM policy
authoring.

The ``pyvmomi`` package is a hard dependency of saltext-vcf. Connect
to vCenter (or directly to an ESXi host) once per (host, username) pair
and cache the ``ServiceInstance``. Modules call :func:`get_service_instance`
and operate on ``si.content`` to reach the various managers.

Config is read from Salt opts/pillar under the same ``saltext.vcf.vcenter``
key as ``utils/vcenter`` (REST), so REST and SOAP modules share one
credential block::

    saltext.vcf:
      vcenter:
        host: mgmt-vc.example.test
        username: administrator@vsphere.local
        password: secret
        verify_ssl: false
"""

import atexit
import logging
import ssl
import time

from pyVim.connect import Disconnect
from pyVim.connect import SmartConnect
from pyVmomi import vim as _vim

from saltext.vcf.utils import vcenter as vc_rest

log = logging.getLogger(__name__)

# Cached ServiceInstance per (host, username). pyVmomi sessions are
# heavier than REST tokens; reusing them across calls saves ~150ms each.
_SI_CACHE: dict[str, object] = {}


def get_config(opts, profile=None):
    """SOAP shares the REST vCenter config — no separate pillar key."""
    return vc_rest.get_config(opts, profile=profile)


def get_service_instance(opts, profile=None):
    """Return a connected pyVmomi ``ServiceInstance``.

    Cached per ``(host, username)``. Use ``invalidate_service_instance``
    to force a fresh connection (e.g. after a session timeout).

    When ``saltext.vcf.vcenter`` is unset but ``saltext.vcf.esxi`` is,
    delegate to :func:`saltext.vcf.utils.esxi.get_service_instance` so
    every ``vim_*`` client works transparently against a standalone
    ESXi host.  ``saltext.vcf.vcenter`` wins when both are set.
    """
    cfg = get_config(opts, profile=profile)
    if not cfg.get("host"):
        # Fall back to the ESXi standalone helper's ServiceInstance.
        from saltext.vcf.utils import esxi as esxi_conn  # noqa: PLC0415

        return esxi_conn.get_service_instance(opts, profile=profile)
    host, port, username = _connection_target(cfg)
    cache_key = f"{host}:{port or 443}:{username}"

    if cache_key in _SI_CACHE:
        return _SI_CACHE[cache_key]

    sslContext = None  # pylint: disable=invalid-name
    if not cfg["verify_ssl"]:
        sslContext = ssl._create_unverified_context()  # pylint: disable=invalid-name

    smart_kwargs = {
        "host": host,
        "user": username,
        "pwd": cfg["password"],
        "sslContext": sslContext,
    }
    if port is not None:
        smart_kwargs["port"] = int(port)
    si = SmartConnect(**smart_kwargs)
    _SI_CACHE[cache_key] = si
    atexit.register(_safe_disconnect, si)
    return si


def invalidate_service_instance(opts, profile=None):
    """Disconnect and drop the cached ServiceInstance for this target."""
    cfg = get_config(opts, profile=profile)
    host, port, username = _connection_target(cfg)
    cache_key = f"{host}:{port or 443}:{username}"
    si = _SI_CACHE.pop(cache_key, None)
    if si is not None:
        _safe_disconnect(si)


def _connection_target(cfg):
    """Return ``(host, port, username)`` parsed from a pillar ``cfg`` block.

    Allows ``host: localhost:25443`` style or an explicit ``port:`` key in
    the pillar config — useful when reaching the target through an SSH
    tunnel or other port-forward.
    """
    host = cfg["host"]
    username = cfg["username"]
    port = cfg.get("port")
    if ":" in host and port is None:
        host, _, port_str = host.rpartition(":")
        port = int(port_str)
    return host, port, username


def _safe_disconnect(si):
    try:
        Disconnect(si)
    except Exception as exc:  # pylint: disable=broad-except
        log.debug("pyVmomi disconnect raised %s; ignoring", exc)


def content(opts, profile=None):
    """Shortcut: ``get_service_instance(opts).RetrieveContent()``."""
    return get_service_instance(opts, profile=profile).RetrieveContent()


def is_standalone_esxi(opts, profile=None):
    """Return True when only ``saltext.vcf.esxi`` (no vCenter) is configured.

    The two SOAP entry points diverge in credential source and host-lookup
    semantics; ``vim_*`` clients use this to route through
    :mod:`saltext.vcf.utils.esxi` for standalone hosts.
    """
    # Local import to avoid a circular module dep when utils.esxi does the
    # (rare) reverse consultation.
    from saltext.vcf.utils import esxi as esxi_conn  # noqa: PLC0415
    from saltext.vcf.utils import vcenter as vcenter_conn  # noqa: PLC0415

    vc = vcenter_conn.get_config(opts, profile=profile)
    esxi = esxi_conn.get_config(opts, profile=profile)
    return bool(esxi.get("host")) and not vc.get("host")


def resolve_host_system(opts, name_or_id, profile=None):
    """Locate a ``vim.HostSystem`` for both standalone and vCenter modes.

    Shared helper used by every ``vim_host_*`` client — one place to update
    resolution rules.

    Match order:

    1. ``host._moId`` or ``host.name``
    2. Any VMkernel VNIC's ``ipAddress`` — useful when the caller only
       knows the mgmt IP the SmartConnect was made against but the host's
       ``name`` is a stale DHCP-inherited hostname.
    3. Standalone-mode fallback: if only one HostSystem exists in the
       entire tree, return it.  ``h.name`` on a fresh-install ESXi is
       often an inherited DHCP hostname (``sysrescue``, etc.) and
       ``h._moId`` is a fixed ``ha-host`` — both are impractical to
       target by.
    """
    # Local import: pyvmomi is a hard dep; ``vim`` shadows the module name.
    from pyVmomi import vim as _vim  # noqa: PLC0415

    if is_standalone_esxi(opts, profile=profile):
        from saltext.vcf.utils import esxi as esxi_conn  # noqa: PLC0415

        si = esxi_conn.get_service_instance(opts, profile=profile)
        service_content = si.RetrieveContent()
    else:
        service_content = content(opts, profile=profile)
    container = service_content.viewManager.CreateContainerView(
        service_content.rootFolder, [_vim.HostSystem], True
    )
    try:
        hosts = list(container.view)
        for h in hosts:
            if name_or_id in (h._moId, h.name):  # noqa: SLF001
                return h
        for h in hosts:
            try:
                vnics = (h.config.network.vnic if h.config and h.config.network else []) or []
            except AttributeError:
                continue
            for vnic in vnics:
                ip = getattr(getattr(vnic.spec, "ip", None), "ipAddress", None)
                if ip and ip == name_or_id:
                    return h
        if is_standalone_esxi(opts, profile=profile) and len(hosts) == 1:
            return hosts[0]
    finally:
        container.Destroy()
    raise LookupError(f"host {name_or_id!r} not found")


# ---------------------------------------------------------------------------
# Manager accessors — convenience for callers
# ---------------------------------------------------------------------------


def alarm_manager(opts, profile=None):
    return content(opts, profile=profile).alarmManager


def perf_manager(opts, profile=None):
    return content(opts, profile=profile).perfManager


def extension_manager(opts, profile=None):
    return content(opts, profile=profile).extensionManager


def license_manager(opts, profile=None):
    return content(opts, profile=profile).licenseManager


def license_assignment_manager(opts, profile=None):
    return license_manager(opts, profile=profile).licenseAssignmentManager


def custom_fields_manager(opts, profile=None):
    return content(opts, profile=profile).customFieldsManager


def property_collector(opts, profile=None):
    return content(opts, profile=profile).propertyCollector


def view_manager(opts, profile=None):
    return content(opts, profile=profile).viewManager


def root_folder(opts, profile=None):
    return content(opts, profile=profile).rootFolder


def authorization_manager(opts, profile=None):
    return content(opts, profile=profile).authorizationManager


def wait_for_task(task, *, timeout=300, poll_interval=0.5):
    """Block until a pyVmomi ``*_Task`` finishes, then return ``task.info.result``.

    pyVmomi's ``*_Task`` methods are async: they return as soon as vCenter
    accepts the request, before the operation has actually taken effect.
    Callers that immediately query the resulting state race the task; wrap
    every mutating SOAP call with this helper.

    Polls ``task.info.state`` every ``poll_interval`` seconds (default 0.5)
    up to ``timeout`` seconds (default 300). Raises ``RuntimeError`` on task
    error and ``TimeoutError`` if the task hasn't finished in time.
    """
    deadline = time.monotonic() + timeout
    while task.info.state in (_vim.TaskInfo.State.running, _vim.TaskInfo.State.queued):
        if time.monotonic() > deadline:
            raise TimeoutError(
                f"task {task._moId!r} did not finish within {timeout}s"  # noqa: SLF001
            )
        time.sleep(poll_interval)
    if task.info.state == _vim.TaskInfo.State.error:
        msg = task.info.error.msg if task.info.error else "task failed"
        raise RuntimeError(f"task {task._moId!r} failed: {msg}")  # noqa: SLF001
    return task.info.result


def session_cookie(opts, profile=None):
    """Return the ``vmware_soap_session`` cookie from the cached ServiceInstance.

    Used to authenticate HTTP requests to vCenter ``/folder/?dsName=…`` style
    file-transfer endpoints (datastore upload/download, OVF push/pull).
    The cookie value is wrapped as ``vmware_soap_session=<token>`` ready for
    a ``Cookie`` header.
    """
    si = get_service_instance(opts, profile=profile)
    stub = si._stub  # noqa: SLF001
    raw_cookie = stub.cookie
    # pyVmomi formats it as: vmware_soap_session="<token>"; Path=/; ...
    # Extract just the name=value pair, stripping quotes.
    pair = raw_cookie.split(";", 1)[0]
    name, _, value = pair.partition("=")
    return f"{name}={value.strip().strip(chr(34))}"
