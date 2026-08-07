"""vCenter folder (organizational hierarchy).

REST (``/api/vcenter/folder``) is read-only — list/get/list_by_type only.
vCenter has never exposed folder create/delete through the modern vAPI
surface; the only path is SOAP ``Folder.CreateFolder`` / ``Folder.Destroy_Task``,
so :func:`create` and :func:`delete` go through :mod:`saltext.vcf.utils.vim`
instead of :mod:`saltext.vcf.utils.vcenter`.
"""

import requests
from pyVmomi import vim

from saltext.vcf.utils import vcenter
from saltext.vcf.utils import vim as soap

PATH = "/api/vcenter/folder"

# Maps the REST ``type`` filter value to the vim.Datacenter attribute that
# holds that type's top-level folder.
_ROOT_ATTR = {
    "VIRTUAL_MACHINE": "vmFolder",
    "HOST": "hostFolder",
    "NETWORK": "networkFolder",
    "DATASTORE": "datastoreFolder",
}


def list_(opts, profile=None):
    return vcenter.api_get(opts, PATH, profile=profile)


def get(opts, folder_id, profile=None):
    return vcenter.api_get(opts, f"{PATH}/{folder_id}", profile=profile)


def get_or_none(opts, folder_id, profile=None):
    try:
        return get(opts, folder_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def list_by_type(opts, folder_type, profile=None):
    """``folder_type``: DATACENTER, DATASTORE, HOST, NETWORK, VIRTUAL_MACHINE."""
    return vcenter.api_get(opts, PATH, params={"type": folder_type}, profile=profile)


def find_by_name(opts, name, profile=None):
    """Return ``{"folder": <moId>, "name": name}`` for the first folder named
    *name*, or ``None``. Resolved via SOAP since the REST list responses
    don't carry ``name``.
    """
    obj = _find_folder_object(opts, name, profile=profile)
    if obj is None:
        return None
    return {"folder": obj._moId, "name": obj.name}  # noqa: SLF001


def create(opts, name, folder_type, parent=None, datacenter=None, profile=None):
    """Create a folder named *name* of *folder_type* and return its moId.

    *folder_type* is one of ``VIRTUAL_MACHINE``, ``HOST``, ``NETWORK``,
    ``DATASTORE`` (top-level datacenter folders aren't created this way —
    use ``vim.Folder.CreateFolder`` on ``content.rootFolder`` directly if
    that's ever needed). *parent* nests the new folder under an existing
    folder found by name; otherwise it's created at *datacenter*'s
    *folder_type* root.
    """
    parent_obj = _resolve_parent(
        opts, folder_type, parent=parent, datacenter=datacenter, profile=profile
    )
    new_folder = parent_obj.CreateFolder(name=name)
    return new_folder._moId  # noqa: SLF001


def delete(opts, folder_id, profile=None):
    """Delete the folder with moId *folder_id*. Fails if the folder isn't empty."""
    obj = _folder_by_moid(opts, folder_id, profile=profile)
    task = obj.Destroy_Task()
    soap.wait_for_task(task)


def _folder_by_moid(opts, moid, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.Folder], True)
    try:
        for f in container.view:
            if f._moId == moid:  # noqa: SLF001
                return f
    finally:
        container.Destroy()
    raise LookupError(f"folder {moid!r} not found")


def _find_folder_object(opts, name, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.Folder], True)
    try:
        for f in container.view:
            if f.name == name:
                return f
    finally:
        container.Destroy()
    return None


def _find_datacenter(opts, name, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datacenter], True)
    try:
        for dc in container.view:
            if name in (dc._moId, dc.name):  # noqa: SLF001
                return dc
    finally:
        container.Destroy()
    raise LookupError(f"datacenter {name!r} not found")


def _resolve_parent(opts, folder_type, parent=None, datacenter=None, profile=None):
    if parent:
        obj = _find_folder_object(opts, parent, profile=profile)
        if obj is None:
            raise LookupError(f"parent folder {parent!r} not found")
        return obj

    attr = _ROOT_ATTR.get(folder_type)
    if attr is None:
        raise ValueError(f"unknown folder_type {folder_type!r}")
    if not datacenter:
        raise ValueError(f"datacenter is required to create a top-level {folder_type} folder")

    dc = _find_datacenter(opts, datacenter, profile=profile)
    return getattr(dc, attr)
