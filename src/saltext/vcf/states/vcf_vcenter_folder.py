"""State module for vCenter folders."""

from saltext.vcf.clients import vcenter_folder as c

__virtualname__ = "vcf_vcenter_folder"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(name, folder_type, parent=None, datacenter=None, profile=None):
    """Ensure a folder named *name* of *folder_type* exists.

    *folder_type* is one of ``VIRTUAL_MACHINE``, ``HOST``, ``NETWORK``,
    ``DATASTORE``. When *parent* is given, the folder is nested under that
    (existing) folder by name; otherwise it's created at *datacenter*'s
    *folder_type* root.
    """
    ret = _ret(name)
    existing = c.find_by_name(__opts__, name, profile=profile)
    if existing is not None:
        ret["comment"] = f"folder {name} already exists"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"folder {name} would be created"
        return ret
    folder_id = c.create(
        __opts__, name, folder_type, parent=parent, datacenter=datacenter, profile=profile
    )
    ret["changes"] = {"new": folder_id}
    ret["comment"] = f"folder {name} created"
    return ret


def absent(name, profile=None):
    """Ensure no folder named *name* exists.

    Fails if the folder still contains child objects — remove/relocate
    those first (vCenter's own ``Destroy_Task`` behavior).
    """
    ret = _ret(name)
    existing = c.find_by_name(__opts__, name, profile=profile)
    if existing is None:
        ret["comment"] = f"folder {name} is already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"folder {name} would be deleted"
        return ret
    c.delete(__opts__, existing["folder"], profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"folder {name} deleted"
    return ret
