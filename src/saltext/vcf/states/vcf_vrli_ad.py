"""State module for vRLI Active Directory integration.

Idempotency: the server never returns the ``password`` field, so we
match on the caller-supplied ``domain`` / ``username`` /
``connType`` triple (plus ``enableAD``). When ``force`` is true the
POST is issued even if the tri-key matches — useful for password
rotations, where the caller is the only authority on drift.
"""

from saltext.vcf.clients import vrli_ad as c

__virtualname__ = "vcf_vrli_ad"

_MATCH_FIELDS = ("enableAD", "domain", "username", "connType")


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def ad_configured(
    name,
    domain,
    username,
    password,
    conn_type="STANDARD",
    ldap_servers=None,
    enable_ad=True,
    force=False,
    profile=None,
):
    """Ensure the AD integration is configured to the given tri-key.

    ``ldap_servers`` is only accepted / passed through when
    ``conn_type`` is ``CUSTOM``; the server ignores it for
    ``STANDARD`` / ``GLOBAL_CAT``. The camelCase kwargs
    ``connType`` / ``enableAD`` are also accepted as legacy aliases
    that mirror the raw API field names.
    """
    ret = _ret(name)
    spec = {
        "enableAD": bool(enable_ad),
        "domain": domain,
        "username": username,
        "password": password,
        "connType": conn_type,
    }
    if ldap_servers and conn_type == "CUSTOM":
        spec["ldapServers"] = list(ldap_servers)

    current = c.get(__opts__, profile=profile) or {}
    matches = all(current.get(k) == spec.get(k) for k in _MATCH_FIELDS)
    if matches and not force:
        ret["comment"] = f"AD already configured for domain {domain!r} on {conn_type}"
        return ret
    if __opts__.get("test"):
        ret["result"] = None
        ret["comment"] = f"AD would be reconfigured for domain {domain!r} on {conn_type}"
        return ret
    c.set_(__opts__, spec, profile=profile)
    ret["changes"] = {
        k: {"old": current.get(k), "new": spec[k]}
        for k in _MATCH_FIELDS
        if current.get(k) != spec[k]
    } or {"password": "rotated"}
    ret["comment"] = f"AD configured for domain {domain!r} ({conn_type})"
    return ret


def ad_disabled(name, profile=None):
    """Ensure the AD integration is disabled."""
    ret = _ret(name)
    current = c.get(__opts__, profile=profile) or {}
    if not current.get("enableAD"):
        ret["comment"] = "AD already disabled"
        return ret
    if __opts__.get("test"):
        ret["result"] = None
        ret["comment"] = "AD would be disabled"
        return ret
    c.disable(__opts__, profile=profile)
    ret["changes"] = {"enableAD": {"old": True, "new": False}}
    ret["comment"] = "AD disabled"
    return ret
