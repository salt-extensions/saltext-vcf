"""State module for VCF Operations stored credentials.

Identity for matching existing credentials is the ``name`` field (within
``adapterKindKey`` / ``credentialKindKey``). The Suite-API returns a
server-assigned ``id`` we read but don't accept as user-facing input.
"""

from saltext.vmware.clients import vcfops_credential as c

__virtualname__ = "vmware_vcfops_credential"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def _find_existing(name, adapter_kind, credential_kind, profile=None):
    body = c.list_(__opts__, profile=profile)
    elements = body.get("credentialInstances") if isinstance(body, dict) else None
    if not elements:
        return None
    for entry in elements:
        if (
            entry.get("name") == name
            and entry.get("adapterKindKey") == adapter_kind
            and entry.get("credentialKindKey") == credential_kind
        ):
            return entry
    return None


def present(name, adapter_kind, credential_kind, fields, profile=None):
    """Ensure a credential record ``(name, adapter_kind, credential_kind)`` exists.

    *fields* is a list of ``{"name": ..., "value": ...}`` pairs matching
    the credential kind's schema.
    """
    ret = _ret(name)
    spec = {
        "name": name,
        "adapterKindKey": adapter_kind,
        "credentialKindKey": credential_kind,
        "fields": fields,
    }
    existing = _find_existing(name, adapter_kind, credential_kind, profile=profile)
    if existing is not None:
        ret["comment"] = f"Credential {name} already present"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Credential {name} would be created"
        return ret
    c.create(__opts__, spec, profile=profile)
    ret["changes"] = {"new": name}
    ret["comment"] = f"Credential {name} created"
    return ret


def absent(name, adapter_kind, credential_kind, profile=None):
    ret = _ret(name)
    existing = _find_existing(name, adapter_kind, credential_kind, profile=profile)
    if existing is None:
        ret["comment"] = f"Credential {name} already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Credential {name} would be deleted"
        return ret
    c.delete(__opts__, existing["id"], profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"Credential {name} deleted"
    return ret
