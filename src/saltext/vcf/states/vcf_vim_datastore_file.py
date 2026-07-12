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


def _file_size_on_ds(file_list, basename):
    for entry in file_list:
        if entry["path"] == basename:
            return entry.get("fileSize") or entry.get("size")
    return None


def file_present(
    name,
    datacenter,
    datastore,
    ds_path,
    source,
    profile=None,
    force=False,
    match_size=False,
):
    """Ensure ``[datastore] ds_path`` exists, uploading from *source* if missing.

    * *force* — always re-upload, even if the file already exists.
    * *match_size* — treat a size-mismatch (local vs. datastore) as
      drift and re-upload.  Cheaper than a content diff; catches most
      "regenerated on disk, needs re-upload" cases (ISO rebuilds,
      kickstart re-renders).

    Content drift beyond size is NOT checked — for tight config
    reconciliation, run this alongside a rendered-file state that
    detects local changes and set ``force=True`` on watch.
    """
    ret = _ret(name)
    import os
    parent, basename = _split(ds_path)
    listing = c.list_(__opts__, datacenter, datastore, path=parent, profile=profile)
    exists = _file_present(listing, basename)
    if exists and not force and not match_size:
        ret["comment"] = f"{ds_path} already present on [{datastore}]"
        return ret
    reason = "missing"
    if exists:
        if force:
            reason = "force"
        elif match_size:
            local_size = os.path.getsize(source)
            ds_size = _file_size_on_ds(listing, basename)
            if ds_size == local_size:
                ret["comment"] = (
                    f"{ds_path} present on [{datastore}] "
                    f"({local_size} bytes match)"
                )
                return ret
            reason = f"size drift local={local_size} ds={ds_size}"
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"would upload {source} → [{datastore}] {ds_path} ({reason})"
        return ret
    if exists:
        c.delete(__opts__, datacenter, datastore, ds_path, profile=profile)
    c.upload(__opts__, datacenter, datastore, source, ds_path, profile=profile)
    ret["changes"] = {"uploaded": ds_path, "reason": reason}
    ret["comment"] = f"uploaded {source} → [{datastore}] {ds_path} ({reason})"
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
