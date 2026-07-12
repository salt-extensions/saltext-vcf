"""Datastore file transfer + manipulation.

Three surfaces are used:

* ``Datastore.browser.SearchDatastore_Task`` for listings
* ``FileManager`` for delete / mkdir / move (rename or copy across datastores)
* HTTP ``/folder/<ds_path>?dcPath=<dc>&dsName=<ds>`` for upload/download,
  authenticated via the SOAP session cookie from
  :func:`saltext.vcf.utils.vim.session_cookie`
"""

from pathlib import Path

import requests
from pyVmomi import vim

from saltext.vcf.utils import esxi as esxi_conn
from saltext.vcf.utils import vcenter as vc_rest
from saltext.vcf.utils import vim as soap


def _http_endpoint(opts, profile=None):
    """Return the (host, verify_ssl) tuple for the datastore HTTP endpoint.

    Standalone-ESXi has no vCenter config; fall back to the ESXi block.
    Mirrors the delegation ``soap.get_service_instance`` does for SOAP.
    """
    if soap.is_standalone_esxi(opts, profile=profile):
        cfg = esxi_conn.get_config(opts, profile=profile)
    else:
        cfg = vc_rest.get_config(opts, profile=profile)
    return cfg["host"], cfg.get("verify_ssl", False)


def _find_datacenter(opts, name_or_id, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datacenter], True)
    try:
        for dc in container.view:
            if name_or_id in (dc._moId, dc.name):  # noqa: SLF001
                return dc
    finally:
        container.Destroy()
    raise LookupError(f"datacenter {name_or_id!r} not found")


def _find_datastore(opts, name_or_id, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datastore], True)
    try:
        for ds in container.view:
            if name_or_id in (ds._moId, ds.name):  # noqa: SLF001
                return ds
    finally:
        container.Destroy()
    raise LookupError(f"datastore {name_or_id!r} not found")


def _file_manager(opts, profile=None):
    return soap.content(opts, profile=profile).fileManager


def _ds_path(datastore_name, path):
    """Build a ``[datastore] path`` reference string accepted by FileManager APIs."""
    return f"[{datastore_name}] {path.lstrip('/')}"


def _folder_url(host, ds_path, dc_name, datastore_name):
    """Compose the HTTP ``/folder`` URL for upload/download."""
    p = ds_path.lstrip("/")
    return f"https://{host}/folder/{p}?dcPath={dc_name}&dsName={datastore_name}"


def list_(opts, datacenter, datastore, path="", profile=None):
    """Return ``[{path, file_type, size, modification, owner}, ...]`` for files under *path*."""
    ds = _find_datastore(opts, datastore, profile=profile)
    browser = ds.browser
    spec = vim.host.DatastoreBrowser.SearchSpec()
    spec.matchPattern = ["*"]
    spec.details = vim.host.DatastoreBrowser.FileInfo.Details(
        fileType=True, fileSize=True, modification=True, fileOwner=True
    )
    target = _ds_path(datastore, path)
    task = browser.SearchDatastore_Task(datastorePath=target, searchSpec=spec)
    while task.info.state in (vim.TaskInfo.State.running, vim.TaskInfo.State.queued):
        pass  # rely on the SOAP session keeping order; tests mock this
    if task.info.state == vim.TaskInfo.State.error:
        raise RuntimeError(task.info.error.msg if task.info.error else "search failed")
    result = task.info.result
    out = []
    for entry in result.file or []:
        out.append(
            {
                "path": entry.path,
                "file_type": type(entry).__name__,
                "size": int(entry.fileSize) if entry.fileSize is not None else None,
                "modification": (entry.modification.isoformat() if entry.modification else None),
                "owner": entry.owner,
            }
        )
    return out


def delete(opts, datacenter, datastore, path, profile=None):
    """Delete a file or directory. Returns the vim.Task moId."""
    dc = _find_datacenter(opts, datacenter, profile=profile)
    fm = _file_manager(opts, profile=profile)
    task = fm.DeleteDatastoreFile_Task(name=_ds_path(datastore, path), datacenter=dc)
    return task._moId  # noqa: SLF001


def mkdir(opts, datacenter, datastore, path, *, create_parents=True, profile=None):
    """Create a directory on the datastore. Synchronous (FileManager.MakeDirectory)."""
    dc = _find_datacenter(opts, datacenter, profile=profile)
    fm = _file_manager(opts, profile=profile)
    fm.MakeDirectory(
        name=_ds_path(datastore, path),
        datacenter=dc,
        createParentDirectories=bool(create_parents),
    )
    return True


def move(
    opts,
    src_datacenter,
    src_datastore,
    src_path,
    dst_datacenter,
    dst_datastore,
    dst_path,
    *,
    force=False,
    profile=None,
):
    """Move a file across datastores. Returns the vim.Task moId."""
    src_dc = _find_datacenter(opts, src_datacenter, profile=profile)
    dst_dc = _find_datacenter(opts, dst_datacenter, profile=profile)
    fm = _file_manager(opts, profile=profile)
    task = fm.MoveDatastoreFile_Task(
        sourceName=_ds_path(src_datastore, src_path),
        sourceDatacenter=src_dc,
        destinationName=_ds_path(dst_datastore, dst_path),
        destinationDatacenter=dst_dc,
        force=bool(force),
    )
    return task._moId  # noqa: SLF001


def upload(opts, datacenter, datastore, local_path, ds_path, profile=None):
    """Stream a local file to ``[datastore] ds_path`` via HTTPS POST.

    The HTTP request is authenticated with the SOAP session cookie. Returns the
    HTTP status code on success.
    """
    host, verify_ssl = _http_endpoint(opts, profile=profile)
    cookie = soap.session_cookie(opts, profile=profile)
    url = _folder_url(host, ds_path, datacenter, datastore)
    headers = {"Content-Type": "application/octet-stream", "Cookie": cookie}
    with open(local_path, "rb") as fp:
        resp = requests.put(
            url,
            data=fp,
            headers=headers,
            verify=verify_ssl,
            timeout=600,
        )
    resp.raise_for_status()
    return resp.status_code


def download(opts, datacenter, datastore, ds_path, local_path, profile=None):
    """Stream ``[datastore] ds_path`` to disk via HTTPS GET. Returns the byte count written."""
    host, verify_ssl = _http_endpoint(opts, profile=profile)
    cookie = soap.session_cookie(opts, profile=profile)
    url = _folder_url(host, ds_path, datacenter, datastore)
    headers = {"Cookie": cookie}
    written = 0
    with requests.get(url, headers=headers, verify=verify_ssl, timeout=600, stream=True) as resp:
        resp.raise_for_status()
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, "wb") as fp:
            for chunk in resp.iter_content(chunk_size=1024 * 64):
                if chunk:
                    fp.write(chunk)
                    written += len(chunk)
    return written
