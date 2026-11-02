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


def renamed(name, new_name, profile=None):
    """Ensure the folder *name* is renamed to *new_name*.

    .. code-block:: yaml

        Rename folder:
          vcf_vcenter_folder.renamed:
            - name: staging
            - new_name: archive
    """
    ret = _ret(name)
    existing = c.find_by_name(__opts__, name, profile=profile)
    if existing is None:
        ret["result"] = False
        ret["comment"] = f"folder {name!r} not found"
        return ret
    if c.find_by_name(__opts__, new_name, profile=profile) is not None:
        ret["comment"] = f"folder {new_name!r} already exists (rename may have already run)."
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"folder {name!r} would be renamed to {new_name!r}."
        ret["changes"] = {"name": (name, new_name)}
        return ret
    c.rename(__opts__, name, new_name, profile=profile)
    ret["changes"] = {"name": (name, new_name)}
    ret["comment"] = f"folder {name!r} renamed to {new_name!r}."
    return ret


def moved(name, destination_folder_name, profile=None):
    """Ensure folder *name* is nested under *destination_folder_name*.

    .. code-block:: yaml

        Move folder:
          vcf_vcenter_folder.moved:
            - name: staging
            - destination_folder_name: archive
    """
    ret = _ret(name)
    existing = c.find_by_name(__opts__, name, profile=profile)
    if existing is None:
        ret["result"] = False
        ret["comment"] = f"folder {name!r} not found"
        return ret
    # Detect the current parent via the SOAP walk (the REST get carries moid only).
    current_parent = c.parent_name(__opts__, existing["folder"], profile=profile)
    if current_parent == destination_folder_name:
        ret["comment"] = f"folder {name!r} already under {destination_folder_name!r}."
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"folder {name!r} would be moved under {destination_folder_name!r}."
        ret["changes"] = {"parent": (current_parent, destination_folder_name)}
        return ret
    c.move(__opts__, name, destination_folder_name, profile=profile)
    ret["changes"] = {"parent": (current_parent, destination_folder_name)}
    ret["comment"] = f"folder {name!r} moved under {destination_folder_name!r}."
    return ret
