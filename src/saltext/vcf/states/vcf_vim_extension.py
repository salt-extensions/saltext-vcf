"""State module for vCenter extension/plugin registration (SOAP)."""

from saltext.vcf.clients import vim_extension as c

__virtualname__ = "vcf_vim_extension"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def registered(name, version, description, company, profile=None, **fields):
    """Ensure an extension with key *name* is registered with the given metadata."""
    ret = _ret(name)
    current = c.get_or_none(__opts__, name, profile=profile)
    if current is not None:
        # Match on version+description (the typical drift signal)
        if (
            current.get("version") == version
            and current.get("description") == description
            and current.get("company") == company
        ):
            ret["comment"] = f"Extension {name} already registered as {version}"
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"Extension {name} would be updated"
            return ret
        c.update(
            __opts__,
            name,
            version=version,
            description=description,
            profile=profile,
            **fields,
        )
        ret["changes"] = {
            "version": {"old": current.get("version"), "new": version},
            "description": {"old": current.get("description"), "new": description},
        }
        ret["comment"] = f"Extension {name} updated"
        return ret

    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Extension {name} would be registered"
        return ret
    c.register(__opts__, name, version, description, company, profile=profile, **fields)
    ret["changes"] = {"new": name}
    ret["comment"] = f"Extension {name} registered"
    return ret


def unregistered(name, profile=None):
    ret = _ret(name)
    if c.get_or_none(__opts__, name, profile=profile) is None:
        ret["comment"] = f"Extension {name} is already unregistered"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Extension {name} would be unregistered"
        return ret
    c.unregister(__opts__, name, profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"Extension {name} unregistered"
    return ret
