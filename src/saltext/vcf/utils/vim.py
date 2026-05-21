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
        host: mgmt-vc.vcf.nimbus.internal
        username: administrator@vsphere.local
        password: VMware123!VMware123!
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
    """
    cfg = get_config(opts, profile=profile)
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
