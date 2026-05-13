"""
vSphere SOAP/VMODL connection helpers (pyVmomi).

Used for capabilities that vSphere REST doesn't yet expose — vSAN
imperative ops, Auto Deploy, Fault Tolerance, PerfManager historical
counters, PropertyCollector real-time subscriptions, AlarmManager
authoring, ExtensionManager, LicenseAssignmentManager, PBM policy
authoring.

The ``pyvmomi`` package is a hard dependency of saltext-vmware. Connect
to vCenter (or directly to an ESXi host) once per (host, username) pair
and cache the ``ServiceInstance``. Modules call :func:`get_service_instance`
and operate on ``si.content`` to reach the various managers.

Config is read from Salt opts/pillar under the same ``saltext.vmware.vcenter``
key as ``utils/vcenter`` (REST), so REST and SOAP modules share one
credential block::

    saltext.vmware:
      vcenter:
        host: mgmt-vc.vcf.nimbus.internal
        username: administrator@vsphere.local
        password: VMware123!VMware123!
        verify_ssl: false
"""

import atexit
import logging
import ssl

from pyVim.connect import Disconnect
from pyVim.connect import SmartConnect

from saltext.vmware.utils import vcenter as vc_rest

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
    host = cfg["host"]
    username = cfg["username"]
    cache_key = f"{host}:{username}"

    if cache_key in _SI_CACHE:
        return _SI_CACHE[cache_key]

    sslContext = None  # pylint: disable=invalid-name
    if not cfg["verify_ssl"]:
        sslContext = ssl._create_unverified_context()  # pylint: disable=invalid-name

    si = SmartConnect(
        host=host,
        user=username,
        pwd=cfg["password"],
        sslContext=sslContext,
    )
    _SI_CACHE[cache_key] = si
    atexit.register(_safe_disconnect, si)
    return si


def invalidate_service_instance(opts, profile=None):
    """Disconnect and drop the cached ServiceInstance for this target."""
    cfg = get_config(opts, profile=profile)
    cache_key = f"{cfg['host']}:{cfg['username']}"
    si = _SI_CACHE.pop(cache_key, None)
    if si is not None:
        _safe_disconnect(si)


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
