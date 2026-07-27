"""State module for VCF Automation appliance hardening.

Provides three idempotent states satisfying the 912 Controls VCFA items:

* :func:`tls_configured` — pin the appliance TLS protocol list to
  ``["TLSv1.2","TLSv1.3"]`` (or a caller override).
* :func:`service_disabled` — ensure a named appliance service (and
  its port) is disabled.
* :func:`ssh_configured` — pin the SSH daemon state (enabled +
  root-login + admin-login flags).
"""

from saltext.vcf.clients import vcfa_appliance as c

__virtualname__ = "vcf_vcfa_appliance"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


# -- TLS -------------------------------------------------------------------


def tls_configured(name, protocols=None, cipher_suites=None, profile=None):
    """Ensure the appliance TLS profile matches *protocols* / *cipher_suites*.

    ``protocols`` defaults to :data:`~saltext.vcf.clients.vcfa_appliance.DEFAULT_PROTOCOLS`
    (``["TLSv1.2","TLSv1.3"]``). ``cipher_suites`` is only compared if
    the caller supplies it.
    """
    ret = _ret(name)
    desired_protocols = (
        list(protocols) if protocols is not None else list(c.DEFAULT_PROTOCOLS)
    )
    current = c.tls_get(__opts__, profile=profile) or {}
    current_protocols = list(current.get("protocols") or [])

    changes = {}
    if sorted(current_protocols) != sorted(desired_protocols):
        changes["protocols"] = {"old": current_protocols, "new": desired_protocols}
    if cipher_suites is not None:
        current_suites = list(current.get("cipherSuites") or [])
        desired_suites = list(cipher_suites)
        if sorted(current_suites) != sorted(desired_suites):
            changes["cipherSuites"] = {"old": current_suites, "new": desired_suites}

    if not changes:
        ret["comment"] = f"TLS already configured with {desired_protocols!r}"
        return ret

    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"TLS would be updated: {sorted(changes.keys())}"
        return ret

    c.tls_set(
        __opts__, protocols=desired_protocols, cipher_suites=cipher_suites, profile=profile
    )
    ret["changes"] = changes
    ret["comment"] = f"TLS updated: {sorted(changes.keys())}"
    return ret


# -- Services --------------------------------------------------------------


def service_disabled(name, service=None, profile=None):
    """Ensure the named appliance service is disabled (unused-port control).

    ``service`` defaults to *name* so operators can write::

        vcfa-appliance-ftp:
          vcf_vcfa_appliance.service_disabled
    """
    ret = _ret(name)
    svc_name = service or name

    current = c.service_get(__opts__, svc_name, profile=profile)
    if current is None:
        ret["result"] = False
        ret["comment"] = f"unknown appliance service: {svc_name!r}"
        return ret

    if not current.get("enabled", False):
        ret["comment"] = f"service {svc_name!r} already disabled"
        return ret

    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"service {svc_name!r} would be disabled"
        return ret

    c.service_set_enabled(__opts__, svc_name, False, profile=profile)
    ret["changes"] = {"enabled": {"old": True, "new": False}}
    ret["comment"] = f"service {svc_name!r} disabled"
    return ret


def service_enabled(name, service=None, profile=None):
    """Ensure the named appliance service is enabled (mirror of :func:`service_disabled`)."""
    ret = _ret(name)
    svc_name = service or name

    current = c.service_get(__opts__, svc_name, profile=profile)
    if current is None:
        ret["result"] = False
        ret["comment"] = f"unknown appliance service: {svc_name!r}"
        return ret

    if current.get("enabled", False):
        ret["comment"] = f"service {svc_name!r} already enabled"
        return ret

    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"service {svc_name!r} would be enabled"
        return ret

    c.service_set_enabled(__opts__, svc_name, True, profile=profile)
    ret["changes"] = {"enabled": {"old": False, "new": True}}
    ret["comment"] = f"service {svc_name!r} enabled"
    return ret


# -- SSH -------------------------------------------------------------------


def ssh_configured(name, enabled=True, root_enabled=True, admin_enabled=True, profile=None):
    """Ensure the SSH daemon state matches the requested flags.

    Default (``enabled=root_enabled=admin_enabled=True``) satisfies the
    912 Controls requirement that SSH with ROOT for vRLCM and ADMIN
    access must be enabled.
    """
    ret = _ret(name)
    current = c.ssh_get(__opts__, profile=profile) or {}
    desired = {
        "enabled": bool(enabled),
        "rootLogin": bool(root_enabled),
        "adminLogin": bool(admin_enabled),
    }

    changes = {}
    for key, want in desired.items():
        have = bool(current.get(key, False))
        if have != want:
            changes[key] = {"old": have, "new": want}

    if not changes:
        ret["comment"] = f"SSH already configured: {desired}"
        return ret

    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"SSH would be updated: {sorted(changes.keys())}"
        return ret

    c.ssh_set(
        __opts__,
        enabled=enabled,
        root_enabled=root_enabled,
        admin_enabled=admin_enabled,
        profile=profile,
    )
    ret["changes"] = changes
    ret["comment"] = f"SSH updated: {sorted(changes.keys())}"
    return ret
