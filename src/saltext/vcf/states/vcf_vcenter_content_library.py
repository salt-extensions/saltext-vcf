"""State module for vCenter Content Library (local libraries)."""

from saltext.vcf.clients import vcenter_content_library as c

__virtualname__ = "vcf_vcenter_content_library"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def _find_local(opts, name, profile=None):
    for library_id in c.find_libraries(opts, name=name, type="LOCAL", profile=profile) or []:
        return c.get_or_none(opts, library_id, profile=profile)
    return None


def present(name, storage_backings, description=None, profile=None):
    """Ensure a local content library named *name* exists with *storage_backings*."""
    ret = _ret(name)
    existing = _find_local(__opts__, name, profile=profile)
    if existing is not None:
        ret["comment"] = f"content library {name} already exists"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"content library {name} would be created"
        return ret
    spec = {}
    if description is not None:
        spec["description"] = description
    library_id = c.create_local(__opts__, name, storage_backings, profile=profile, **spec)
    ret["changes"] = {"new": library_id}
    ret["comment"] = f"content library {name} created"
    return ret


def absent(name, profile=None):
    """Ensure no local content library named *name* exists."""
    ret = _ret(name)
    existing = _find_local(__opts__, name, profile=profile)
    if existing is None:
        ret["comment"] = f"content library {name} is already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"content library {name} would be deleted"
        return ret
    c.delete_local(__opts__, existing["id"], profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"content library {name} deleted"
    return ret
