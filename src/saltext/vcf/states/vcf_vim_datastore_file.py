"""State module for datastore files + directories."""

from saltext.vcf.clients import vim_datastore_file as c

__virtualname__ = "vcf_vim_datastore_file"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def _file_present(file_list, basename):
    return any(entry["path"] == basename for entry in file_list)


def _split(ds_path):
    """Split ``a/b/c.iso`` into (``a/b``, ``c.iso``)."""
    parts = ds_path.rstrip("/").rsplit("/", 1)
    if len(parts) == 1:
        return "", parts[0]
    return parts[0], parts[1]


def file_present(name, datacenter, datastore, ds_path, source, profile=None):
    """Ensure ``[datastore] ds_path`` exists, uploading from *source* if missing.

    Existence check is a simple listing of the parent dir; the file is
    considered "present" if the basename appears. Content drift is NOT
    checked — this state is for one-shot ISO/template upload.
    """
    ret = _ret(name)
    parent, basename = _split(ds_path)
    listing = c.list_(__opts__, datacenter, datastore, path=parent, profile=profile)
    if _file_present(listing, basename):
        ret["comment"] = f"{ds_path} already present on [{datastore}]"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"would upload {source} → [{datastore}] {ds_path}"
        return ret
    c.upload(__opts__, datacenter, datastore, source, ds_path, profile=profile)
    ret["changes"] = {"uploaded": ds_path}
    ret["comment"] = f"uploaded {source} → [{datastore}] {ds_path}"
    return ret


def file_absent(name, datacenter, datastore, ds_path, profile=None):
    """Ensure ``[datastore] ds_path`` does not exist."""
    ret = _ret(name)
    parent, basename = _split(ds_path)
    listing = c.list_(__opts__, datacenter, datastore, path=parent, profile=profile)
    if not _file_present(listing, basename):
        ret["comment"] = f"{ds_path} already absent on [{datastore}]"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"would delete [{datastore}] {ds_path}"
        return ret
    c.delete(__opts__, datacenter, datastore, ds_path, profile=profile)
    ret["changes"] = {"deleted": ds_path}
    ret["comment"] = f"deleted [{datastore}] {ds_path}"
    return ret


def directory_present(name, datacenter, datastore, ds_path, profile=None):
    """Ensure directory ``[datastore] ds_path`` exists (mkdir -p)."""
    ret = _ret(name)
    parent, basename = _split(ds_path)
    listing = c.list_(__opts__, datacenter, datastore, path=parent, profile=profile)
    if _file_present(listing, basename):
        ret["comment"] = f"{ds_path} already exists on [{datastore}]"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"would create directory [{datastore}] {ds_path}"
        return ret
    c.mkdir(__opts__, datacenter, datastore, ds_path, profile=profile)
    ret["changes"] = {"created": ds_path}
    ret["comment"] = f"created directory [{datastore}] {ds_path}"
    return ret
