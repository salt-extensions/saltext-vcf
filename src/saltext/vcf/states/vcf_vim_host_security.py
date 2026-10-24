"""State module for ESXi local accounts and lockdown mode (vCenter-routed SOAP).

Port of ``vmware_esxi.user_present`` / ``user_absent`` /
``password_present`` / ``lockdown_mode`` states. Host-scoped: operate on
one ESXi host identified by name/MoID (or the standalone host when only
``saltext.vcf.esxi`` is configured).
"""

from saltext.vcf.clients import vim_host_security as c

__virtualname__ = "vcf_vim_host_security"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def user_present(name, host, password=None, description=None, profile=None):
    """Ensure local user *name* exists on *host*.

    Password changes cannot be detected remotely, so an existing user is
    updated (mirrors ``vmware_esxi.user_present`` semantics).

    .. code-block:: yaml

        Local user:
          vcf_vim_host_security.user_present:
            - host: esxi-01
            - name: svc-audit
            - password: s3cret
            - description: audit account
    """
    ret = _ret(name)
    existing = c.user_get_or_none(__opts__, host, name, profile=profile)
    if existing is not None:
        drift = {}
        if description is not None and existing.get("full_name") != description:
            drift["description"] = (existing.get("full_name"), description)
        if password is not None:
            # Cannot read the current password — treat as "will update".
            drift["password"] = ("(existing)", "(new)")
        if not drift:
            ret["comment"] = f"User {name!r} already present on {host}."
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"User {name!r} on {host} would be updated."
            ret["changes"] = drift
            return ret
        c.user_update(
            __opts__,
            host,
            name,
            password=password,
            description=description if description is not None else existing.get("full_name"),
            profile=profile,
        )
        ret["changes"] = drift
        ret["comment"] = f"User {name!r} updated on {host}."
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"User {name!r} would be created on {host}."
        ret["changes"] = {"new": name}
        return ret
    c.user_create(__opts__, host, name, password, description=description or "", profile=profile)
    ret["changes"] = {"new": name}
    ret["comment"] = f"User {name!r} created on {host}."
    return ret


def user_absent(name, host, profile=None):
    """Ensure local user *name* does not exist on *host*.

    .. code-block:: yaml

        Remove local user:
          vcf_vim_host_security.user_absent:
            - host: esxi-01
            - name: svc-audit
    """
    ret = _ret(name)
    if c.user_get_or_none(__opts__, host, name, profile=profile) is None:
        ret["comment"] = f"User {name!r} already absent on {host}."
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"User {name!r} would be removed from {host}."
        ret["changes"] = {"old": name}
        return ret
    c.user_delete(__opts__, host, name, profile=profile)
    ret["changes"] = {"old": name}
    ret["comment"] = f"User {name!r} removed from {host}."
    return ret


def password_present(name, host, password, profile=None):
    """Set the password of local user *name* on *host*.

    .. code-block:: yaml

        Host password:
          vcf_vim_host_security.password_present:
            - host: esxi-01
            - name: root
            - password: NewSecret!
    """
    ret = _ret(name)
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Password for user {name!r} on {host} would change."
        return ret
    c.user_update(__opts__, host, name, password=password, profile=profile)
    ret["changes"] = {"password": ("(existing)", "(new)")}
    ret["comment"] = f"Password for user {name!r} changed on {host}."
    return ret


def lockdown(name, host, enter_lockdown_mode, exception_users=None, profile=None):
    """Ensure the host's lockdown mode is *enter_lockdown_mode* (bool).

    Optionally maintains the exception-user list.

    .. code-block:: yaml

        Lockdown:
          vcf_vim_host_security.lockdown:
            - host: esxi-01
            - enter_lockdown_mode: true
            - exception_users:
                - salt-user
    """
    ret = _ret(name)
    current = c.lockdown_get(__opts__, host, profile=profile)
    desired = "lockdownNormal" if enter_lockdown_mode else "lockdownDisabled"
    drift = {}
    if current["mode"] != desired:
        drift["mode"] = (current["mode"], desired)
    if exception_users is not None and sorted(current.get("exception_users") or []) != sorted(
        exception_users
    ):
        drift["exception_users"] = (current.get("exception_users"), list(exception_users))
    if not drift:
        ret["comment"] = f"Lockdown mode on {host} already matches."
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Lockdown mode on {host} would change: {sorted(drift)}."
        ret["changes"] = drift
        return ret
    if "mode" in drift:
        c.lockdown_set(__opts__, host, desired, profile=profile)
    if "exception_users" in drift:
        c.lockdown_set_exception_users(__opts__, host, list(exception_users), profile=profile)
    ret["changes"] = drift
    ret["comment"] = f"Lockdown mode on {host} updated."
    return ret
