"""VASA storage providers via the SMS endpoint.

VASA (vSphere APIs for Storage Awareness) lets storage arrays publish their
capabilities to vCenter. Providers register via a separate SMS endpoint
(``/sms``). This client provides read-only listing of registered providers.
Registration/unregistration requires more involved spec-building and is
deferred to a future batch.
"""

import logging

from pyVim.connect import SmartConnect

from saltext.vcf.utils import vcenter as vc_rest
from saltext.vcf.utils import vim as soap

log = logging.getLogger(__name__)


def _sms_stub(opts, profile=None):
    """Return an SMS service stub bound to the vCenter VASA endpoint.

    pyVmomi's SMS bindings live in a separate module and require their own
    SmartConnect call against the ``/sms`` endpoint path.
    """
    # Warm the main SOAP session so caching is consistent.
    soap.get_service_instance(opts, profile=profile)
    try:
        import pyVmomi.sms  # pylint: disable=import-outside-toplevel,unused-import  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("pyVmomi sms bindings not available — install pyvmomi[sms]") from exc

    cfg = vc_rest.get_config(opts, profile=profile)
    si2 = SmartConnect(
        host=cfg["host"],
        user=cfg["username"],
        pwd=cfg["password"],
        sslContext=None if cfg["verify_ssl"] else _unverified_context(),
        connectionPoolTimeout=30,
        path="/sms/sdk",
    )
    return si2


def _unverified_context():
    import ssl  # pylint: disable=import-outside-toplevel

    return ssl._create_unverified_context()  # pylint: disable=protected-access


def _provider_to_dict(p):
    info = getattr(p, "providerInfo", None) or getattr(p, "info", None)
    if info is None:
        return {"id": p._moId}  # noqa: SLF001
    return {
        "id": p._moId,  # noqa: SLF001
        "name": getattr(info, "name", None),
        "url": getattr(info, "url", None),
        "version": getattr(info, "vasaVersion", None) or getattr(info, "version", None),
        "vendor": getattr(info, "vendorId", None),
        "status": getattr(info, "status", None),
    }


def list_(opts, profile=None):
    """Return every registered VASA provider as ``[{id, name, url, version, vendor, status}]``.

    Returns an empty list if no provider is registered or the SMS endpoint is
    unreachable (lab envs often have no VASA provider).
    """
    try:
        si = _sms_stub(opts, profile=profile)
    except Exception as exc:  # pylint: disable=broad-except
        log.debug("SMS stub unavailable: %s", exc)
        return []
    try:
        sms_content = si.RetrieveServiceContent()
        mgr = sms_content.storageManager
        return [_provider_to_dict(p) for p in mgr.QueryProvider() or []]
    except Exception as exc:  # pylint: disable=broad-except
        log.debug("VASA QueryProvider failed: %s", exc)
        return []


def get(opts, provider_id, profile=None):
    """Return one VASA provider by moId."""
    for p in list_(opts, profile=profile):
        if p.get("id") == provider_id:
            return p
    raise LookupError(f"VASA provider {provider_id!r} not found")


def get_or_none(opts, provider_id, profile=None):
    try:
        return get(opts, provider_id, profile=profile)
    except LookupError:
        return None
