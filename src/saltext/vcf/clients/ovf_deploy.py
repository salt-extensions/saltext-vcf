"""Deploy an OVA to ESXi or vCenter via pyVmomi ``OvfManager``.

OvfManager.CreateImportSpec converts an OVF descriptor into a per-host
import spec; ``ResourcePool.ImportVApp`` returns an ``HttpNfcLease`` whose
deviceUrl entries are the upload targets for each VMDK referenced in the
OVF. A background thread keeps the lease alive via
``HttpNfcLeaseProgress`` while the disks are HTTPS-PUT to ESXi.

Unlike the rest of ``saltext.vcf.clients``, this module takes connection
parameters explicitly rather than reading from ``opts``/pillar — the OVA
deploy is typically run against a *bare* ESXi host before any vCenter
exists, so pillar-driven session caching doesn't apply.
"""

import logging
import ssl
import tarfile
import tempfile
import threading
import time
from pathlib import Path

import requests
from pyVim.connect import Disconnect
from pyVim.connect import SmartConnect
from pyVmomi import vim

from saltext.vcf.utils.vim import wait_for_task

log = logging.getLogger(__name__)

_CHUNK = 4 * 1024 * 1024
_LEASE_READY_TIMEOUT = 120
_LEASE_PROGRESS_INTERVAL = 30


def deploy_ova(
    *,
    ova_source,
    target_host,
    target_user,
    target_password,
    target_port=443,
    vm_name,
    datastore=None,
    network_map=None,
    ovf_properties=None,
    disk_provisioning="thin",
    deployment_option=None,
    power_on=True,
    verify_ssl=False,
    upload_timeout=3600,
):
    """Deploy an OVA to *target_host* (ESXi standalone or vCenter).

    *ova_source* is a local path or an ``http(s)://`` URL.

    *network_map* maps OVF network names to target network names on the
    host. *ovf_properties* is a dict of property id -> string value
    forwarded as ``vim.KeyValue`` pairs (used for VCF Installer OVA
    properties like ``varoot_password``, ``vami.ip0.*``, etc.).

    Returns ``{vm_name, vm_moid, powered_on, elapsed_sec}``.
    """
    start = time.monotonic()
    si = _connect(target_host, target_user, target_password, target_port, verify_ssl)
    try:
        content = si.RetrieveContent()
        rp, vm_folder, host_ref, ds_ref, network_refs = _resolve_targets(
            content, datastore=datastore, network_map=network_map
        )
        ova_path, cleanup_path = _materialize_ova(ova_source, verify_ssl)
        try:
            with tarfile.open(ova_path) as tar:
                members = list(tar.getmembers())
                ovf_xml = _read_ovf_descriptor(tar, members)
                import_spec, file_items = _create_import_spec(
                    content=content,
                    ovf_xml=ovf_xml,
                    vm_name=vm_name,
                    rp=rp,
                    ds=ds_ref,
                    network_refs=network_refs,
                    ovf_properties=ovf_properties or {},
                    disk_provisioning=disk_provisioning,
                    deployment_option=deployment_option,
                    host_ref=host_ref,
                )
                lease = rp.ImportVApp(spec=import_spec, folder=vm_folder, host=host_ref)
                _wait_lease_ready(lease)
                new_vm = lease.info.entity
                progress = _LeaseProgress(lease)
                try:
                    progress.start()
                    _upload_disks(
                        target_host=target_host,
                        device_urls=list(lease.info.deviceUrl or []),
                        file_items=file_items,
                        tar=tar,
                        members=members,
                        progress=progress,
                        verify_ssl=verify_ssl,
                        timeout=upload_timeout,
                        session_cookie=_session_cookie(si),
                    )
                    progress.set_percent(100)
                    progress.stop()
                    lease.HttpNfcLeaseComplete()
                except BaseException:
                    progress.stop()
                    _abort_lease(lease)
                    raise
        finally:
            if cleanup_path is not None:
                Path(cleanup_path).unlink(missing_ok=True)

        powered_on = False
        if power_on:
            task = new_vm.PowerOnVM_Task()
            wait_for_task(task)
            powered_on = True

        return {
            "vm_name": new_vm.name,
            "vm_moid": new_vm._moId,  # noqa: SLF001
            "powered_on": powered_on,
            "elapsed_sec": round(time.monotonic() - start, 2),
        }
    finally:
        try:
            Disconnect(si)
        except Exception:  # pylint: disable=broad-except
            log.debug("Disconnect raised; ignoring", exc_info=True)


def _connect(host, user, password, port, verify_ssl):
    ssl_context = None
    if not verify_ssl:
        ssl_context = ssl._create_unverified_context()  # pylint: disable=protected-access
    return SmartConnect(
        host=host,
        user=user,
        pwd=password,
        port=int(port),
        sslContext=ssl_context,
    )


def _resolve_targets(content, *, datastore, network_map):
    """Return (resource_pool, vm_folder, host_ref, datastore_ref, network_refs).

    Picks the first datacenter and first host. On a standalone ESXi host
    that's ``ha-datacenter`` and the single ``HostSystem``; on vCenter the
    caller should not pass arbitrary hosts in (this client targets
    bootstrap, not multi-cluster deploys).
    """
    dcs = [c for c in content.rootFolder.childEntity if isinstance(c, vim.Datacenter)]
    if not dcs:
        raise RuntimeError("no datacenter found on target")
    dc = dcs[0]
    cr_host = None
    for cr in dc.hostFolder.childEntity:
        if isinstance(cr, vim.ComputeResource) and cr.host:
            cr_host = (cr, cr.host[0])
            break
    if cr_host is None:
        raise RuntimeError(f"no host found in datacenter {dc.name!r}")
    cr, host_ref = cr_host
    rp = cr.resourcePool
    vm_folder = dc.vmFolder

    ds_ref = None
    for ds in host_ref.datastore:
        if datastore is None or ds.name == datastore:
            ds_ref = ds
            break
    if ds_ref is None:
        if datastore:
            raise LookupError(f"datastore {datastore!r} not found on host {host_ref.name}")
        raise RuntimeError(f"no datastore visible on host {host_ref.name}")

    networks_by_name = {n.name: n for n in host_ref.network}
    network_refs = {}
    for ovf_net, target_net in (network_map or {}).items():
        if target_net not in networks_by_name:
            raise LookupError(
                f"network {target_net!r} not on host {host_ref.name}; "
                f"available: {sorted(networks_by_name)}"
            )
        network_refs[ovf_net] = networks_by_name[target_net]
    return rp, vm_folder, host_ref, ds_ref, network_refs


def _materialize_ova(source, verify_ssl):
    """Return ``(local_path, cleanup_path)``.

    For ``http(s)://`` sources the OVA is streamed to a tempfile and the
    cleanup path is returned for caller-side ``unlink``. For local paths
    no copy is made.
    """
    if source.startswith("http://") or source.startswith("https://"):
        fd, tmp_path = tempfile.mkstemp(suffix=".ova", prefix="vcf-ova-")
        try:
            with requests.get(source, stream=True, verify=verify_ssl, timeout=3600) as resp:
                resp.raise_for_status()
                with open(fd, "wb") as fp:
                    for chunk in resp.iter_content(chunk_size=_CHUNK):
                        if chunk:
                            fp.write(chunk)
        except Exception:
            Path(tmp_path).unlink(missing_ok=True)
            raise
        return tmp_path, tmp_path
    p = Path(source).expanduser()
    if not p.is_file():
        raise FileNotFoundError(source)
    return str(p), None


def _read_ovf_descriptor(tar, members):
    for m in members:
        if m.name.lower().endswith(".ovf"):
            f = tar.extractfile(m)
            if f is None:
                raise RuntimeError(f"could not read {m.name!r} from OVA")
            return f.read().decode("utf-8")
    raise RuntimeError("no .ovf descriptor found in OVA")


def _create_import_spec(
    *,
    content,
    ovf_xml,
    vm_name,
    rp,
    ds,
    network_refs,
    ovf_properties,
    disk_provisioning,
    deployment_option,
    host_ref,
):
    cisp = vim.OvfManager.CreateImportSpecParams()
    cisp.entityName = vm_name
    cisp.diskProvisioning = disk_provisioning
    if host_ref is not None:
        cisp.hostSystem = host_ref
    if deployment_option:
        cisp.deploymentOption = deployment_option
    if network_refs:
        cisp.networkMapping = [
            vim.OvfManager.NetworkMapping(name=ovf_net, network=net_obj)
            for ovf_net, net_obj in network_refs.items()
        ]
    if ovf_properties:
        cisp.propertyMapping = [
            vim.KeyValue(key=k, value=str(v)) for k, v in ovf_properties.items()
        ]
    result = content.ovfManager.CreateImportSpec(
        ovfDescriptor=ovf_xml,
        resourcePool=rp,
        datastore=ds,
        cisp=cisp,
    )
    if result.error:
        msgs = [getattr(e, "msg", None) or str(e) for e in result.error]
        raise RuntimeError(f"OVF import spec generation failed: {msgs}")
    for warn in result.warning or []:
        log.warning("ovf import warning: %s", getattr(warn, "msg", warn))
    return result.importSpec, list(result.fileItem or [])


def _wait_lease_ready(lease, timeout=_LEASE_READY_TIMEOUT):
    deadline = time.monotonic() + timeout
    while True:
        state = lease.state
        if state == vim.HttpNfcLease.State.ready:
            return
        if state == vim.HttpNfcLease.State.error:
            msg = lease.error.msg if lease.error else "unknown"
            raise RuntimeError(f"OVA import lease error: {msg}")
        if time.monotonic() > deadline:
            raise TimeoutError(f"OVA import lease not ready within {timeout}s")
        time.sleep(1)


def _abort_lease(lease):
    try:
        lease.HttpNfcLeaseAbort(fault=vim.fault.SystemError(reason="upload aborted"))
    except Exception:  # pylint: disable=broad-except
        log.debug("HttpNfcLeaseAbort raised; ignoring", exc_info=True)


class _LeaseProgress(threading.Thread):
    """Background thread that pings ``HttpNfcLeaseProgress`` every interval.

    ESXi expires the lease if no progress update arrives within ~5 min, so
    this thread must run for the entire duration of disk upload.
    """

    def __init__(self, lease, interval=_LEASE_PROGRESS_INTERVAL):
        super().__init__(daemon=True, name="ovf-lease-progress")
        self.lease = lease
        self.interval = interval
        self._stop = threading.Event()
        self._percent = 0
        self._lock = threading.Lock()

    def set_percent(self, pct):
        with self._lock:
            self._percent = max(0, min(100, int(pct)))

    def stop(self):
        self._stop.set()
        if self.is_alive():
            self.join(timeout=10)

    def run(self):
        while not self._stop.is_set():
            with self._lock:
                pct = self._percent
            try:
                self.lease.HttpNfcLeaseProgress(pct)
            except Exception as exc:  # pylint: disable=broad-except
                log.warning("HttpNfcLeaseProgress(%d) failed: %s", pct, exc)
            if self._stop.wait(self.interval):
                return


def _session_cookie(si):
    """Extract ``vmware_soap_session=<token>`` cookie from a pyVmomi SI.

    Required on every NFC PUT/GET — ESXi's NFC daemon authenticates
    against the same SOAP session that obtained the lease and returns
    ``403 Forbidden`` without it.
    """
    raw = si._stub.cookie  # noqa: SLF001
    pair = raw.split(";", 1)[0]
    name, _, value = pair.partition("=")
    return f"{name}={value.strip().strip(chr(34))}"


def _upload_disks(
    *,
    target_host,
    device_urls,
    file_items,
    tar,
    members,
    progress,
    verify_ssl,
    timeout,
    session_cookie,
):
    by_dev = {}
    for du in device_urls:
        key = getattr(du, "importKey", None) or du.key
        by_dev[key] = du
    member_by_path = {m.name: m for m in members}
    total_size = sum(int(fi.size or 0) for fi in file_items) or 1
    bytes_sent = 0
    for fi in file_items:
        device_url = by_dev.get(fi.deviceId)
        if device_url is None:
            raise RuntimeError(f"no device URL for OVF file {fi.path!r} (deviceId={fi.deviceId!r})")
        url = device_url.url.replace("*", target_host)
        member = _resolve_member(member_by_path, fi.path)
        size = int(fi.size or member.size)
        stream = tar.extractfile(member)
        if stream is None:
            raise RuntimeError(f"could not extract {fi.path!r} from OVA")
        headers = {
            "Content-Type": (
                "application/x-vnd.vmware-streamVmdk"
                if getattr(fi, "create", False)
                else "application/octet-stream"
            ),
            "Content-Length": str(size),
            "Cookie": session_cookie,
            # ESXi's ha-nfc requires Overwrite even for the empty placeholder
            # the lease just created; without it the daemon 403s before
            # looking at the body.
            "Overwrite": "t",
        }
        reader = _CountingReader(stream, prior_sent=bytes_sent, total=total_size, progress=progress)
        resp = requests.put(url, data=reader, headers=headers, verify=verify_ssl, timeout=timeout)
        if resp.status_code >= 400:
            body = (resp.text or "")[:500]
            raise RuntimeError(
                f"NFC upload of {fi.path!r} failed: HTTP {resp.status_code} {body!r}"
            )
        bytes_sent += size


def _resolve_member(member_by_path, ovf_file_path):
    if ovf_file_path in member_by_path:
        return member_by_path[ovf_file_path]
    base = ovf_file_path.rsplit("/", 1)[-1]
    for name, m in member_by_path.items():
        if name.rsplit("/", 1)[-1] == base:
            return m
    raise LookupError(f"OVA does not contain {ovf_file_path!r}")


class _CountingReader:
    """File-like wrapper that updates the progress thread as bytes are read."""

    def __init__(self, stream, *, prior_sent, total, progress):
        self._stream = stream
        self._prior = prior_sent
        self._total = total
        self._progress = progress
        self._read = 0

    def read(self, n=-1):
        chunk = self._stream.read(_CHUNK if n in (-1, None) else n)
        if chunk:
            self._read += len(chunk)
            self._progress.set_percent(100 * (self._prior + self._read) / self._total)
        return chunk
