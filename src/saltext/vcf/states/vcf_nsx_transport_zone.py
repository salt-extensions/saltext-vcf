"""State module for NSX transport zones."""

from saltext.vcf.clients import nsx_transport_zone as r

__virtualname__ = "vcf_nsx_transport_zone"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(name, zone_type, profile=None, **spec):
    """Ensure an NSX transport zone exists."""
    ret = _ret(name)
    current = r.get_by_name(__opts__, name, profile=profile)  # noqa: F821
    if current is not None:
        current_type = current.get("transport_type")
        if current_type and current_type != zone_type:
            ret["result"] = False
            ret["comment"] = (
                f"Transport zone {name} exists with type {current_type!r}, "
                f"expected {zone_type!r}"
            )
            return ret
        ret["comment"] = f"Transport zone {name} is already present"
        return ret
    if __opts__["test"]:  # noqa: F821
        ret["result"] = None
        ret["comment"] = f"Transport zone {name} would be created"
        return ret
    created = r.create(__opts__, name, zone_type, profile=profile, **spec)  # noqa: F821
    ret["changes"] = {"new": created.get("id") or name}
    ret["comment"] = f"Transport zone {name} created"
    return ret


def absent(name, profile=None):
    """Ensure an NSX transport zone is absent."""
    ret = _ret(name)
    current = r.get_by_name(__opts__, name, profile=profile)  # noqa: F821
    if current is None:
        ret["comment"] = f"Transport zone {name} is already absent"
        return ret
    zone_id = current.get("id") or name
    if __opts__["test"]:  # noqa: F821
        ret["result"] = None
        ret["comment"] = f"Transport zone {name} would be deleted"
        return ret
    r.delete(__opts__, zone_id, profile=profile)  # noqa: F821
    ret["changes"] = {"deleted": zone_id}
    ret["comment"] = f"Transport zone {name} deleted"
    return ret
