"""Datastore Cluster (StoragePod) + Storage DRS via SOAP.

A *datastore cluster* in vSphere UI is a ``vim.StoragePod`` in VMODL. SDRS
config (automation level, IO load balancing, space-utilization thresholds,
per-VM overrides) lives in ``StorageDrsConfigSpec`` and is applied via
``StorageResourceManager.ConfigureStorageDrsForPod_Task``.

Top-level surfaces here:

- ``list_`` / ``get`` / ``get_or_none`` — read existing datastore clusters
- ``create`` — ``Folder.CreateStoragePod`` under the datastore folder
- ``delete`` — ``StoragePod.Destroy_Task``
- ``add_datastore`` / ``remove_datastore`` — move a datastore in/out
- ``sdrs_get`` / ``sdrs_set`` — pod-wide SDRS config
- ``sdrs_vm_override_*`` — per-VM SDRS automation/intra-VM rules
"""

from pyVmomi import vim

from saltext.vmware.utils import vim as soap


def _resolve_pod(opts, name_or_id, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.StoragePod], True)
    try:
        for pod in container.view:
            if name_or_id in (pod._moId, pod.name):  # noqa: SLF001
                return pod
    finally:
        container.Destroy()
    raise LookupError(f"datastore cluster {name_or_id!r} not found")


def _resolve_datastore(opts, name_or_id, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datastore], True)
    try:
        for ds in container.view:
            if name_or_id in (ds._moId, ds.name):  # noqa: SLF001
                return ds
    finally:
        container.Destroy()
    raise LookupError(f"datastore {name_or_id!r} not found")


def _resolve_datacenter(opts, name_or_id, profile=None):
    content = soap.content(opts, profile=profile)
    for dc in content.rootFolder.childEntity:
        if isinstance(dc, vim.Datacenter) and name_or_id in (dc._moId, dc.name):  # noqa: SLF001
            return dc
    raise LookupError(f"datacenter {name_or_id!r} not found")


# ---------------------------------------------------------------------------
# Pod CRUD
# ---------------------------------------------------------------------------


def list_(opts, profile=None):
    """Return summary records for every datastore cluster in vCenter."""
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.StoragePod], True)
    try:
        return [
            {
                "moid": p._moId,  # noqa: SLF001
                "name": p.name,
                "datastore_count": len(p.childEntity or []),
            }
            for p in container.view
        ]
    finally:
        container.Destroy()


def get(opts, name_or_id, profile=None):
    pod = _resolve_pod(opts, name_or_id, profile=profile)
    return {
        "moid": pod._moId,  # noqa: SLF001
        "name": pod.name,
        "datastores": [ds.name for ds in (pod.childEntity or [])],
    }


def get_or_none(opts, name_or_id, profile=None):
    try:
        return get(opts, name_or_id, profile=profile)
    except LookupError:
        return None


def create(opts, name, datacenter, profile=None):
    """Create an empty datastore cluster under *datacenter*'s datastore folder."""
    dc = _resolve_datacenter(opts, datacenter, profile=profile)
    pod = dc.datastoreFolder.CreateStoragePod(name=name)
    return pod._moId  # noqa: SLF001


def delete(opts, name_or_id, profile=None):
    pod = _resolve_pod(opts, name_or_id, profile=profile)
    task = pod.Destroy_Task()
    return task._moId  # noqa: SLF001


# ---------------------------------------------------------------------------
# Pod membership
# ---------------------------------------------------------------------------


def add_datastore(opts, pod, datastore, profile=None):
    """Move *datastore* into *pod*. Synchronous (no task)."""
    pod_ref = _resolve_pod(opts, pod, profile=profile)
    ds_ref = _resolve_datastore(opts, datastore, profile=profile)
    pod_ref.parent.MoveIntoFolder_Task = pod_ref.parent.MoveIntoFolder_Task  # nudge attr resolution
    pod_ref.MoveInto_Task = getattr(pod_ref, "MoveInto_Task", None)
    # vSphere uses Folder.MoveIntoFolder_Task for both regular folders and
    # StoragePods (StoragePod inherits from Folder).
    task = pod_ref.MoveIntoFolder_Task(list=[ds_ref])
    return task._moId  # noqa: SLF001


def remove_datastore(opts, pod, datastore, datacenter, profile=None):
    """Move *datastore* out of *pod* back to *datacenter*'s datastore folder."""
    dc = _resolve_datacenter(opts, datacenter, profile=profile)
    ds_ref = _resolve_datastore(opts, datastore, profile=profile)
    task = dc.datastoreFolder.MoveIntoFolder_Task(list=[ds_ref])
    return task._moId  # noqa: SLF001


# ---------------------------------------------------------------------------
# SDRS config
# ---------------------------------------------------------------------------


def _sdrs_mgr(opts, profile=None):
    content = soap.content(opts, profile=profile)
    return content.storageResourceManager


def sdrs_get(opts, pod, profile=None):
    pod_ref = _resolve_pod(opts, pod, profile=profile)
    cfg = pod_ref.podStorageDrsEntry.storageDrsConfig.podConfig
    return {
        "enabled": bool(cfg.enabled),
        "automation_level": str(cfg.defaultVmBehavior),
        "io_load_balance_enabled": bool(cfg.ioLoadBalanceEnabled),
        "space_utilization_threshold": (
            int(cfg.spaceLoadBalanceConfig.spaceUtilizationThreshold)
            if cfg.spaceLoadBalanceConfig
            else None
        ),
    }


def sdrs_set(
    opts,
    pod,
    enabled=None,
    automation_level=None,
    io_load_balance_enabled=None,
    space_utilization_threshold=None,
    profile=None,
):
    """Update the pod-wide SDRS config. Only non-None fields are touched."""
    pod_ref = _resolve_pod(opts, pod, profile=profile)
    pod_cfg = vim.storageDrs.PodConfigSpec()
    if enabled is not None:
        pod_cfg.enabled = bool(enabled)
    if automation_level is not None:
        pod_cfg.defaultVmBehavior = automation_level
    if io_load_balance_enabled is not None:
        pod_cfg.ioLoadBalanceEnabled = bool(io_load_balance_enabled)
    if space_utilization_threshold is not None:
        slb = vim.storageDrs.SpaceLoadBalanceConfig()
        slb.spaceUtilizationThreshold = int(space_utilization_threshold)
        pod_cfg.spaceLoadBalanceConfig = slb
    spec = vim.storageDrs.ConfigSpec(podConfigSpec=pod_cfg)
    mgr = _sdrs_mgr(opts, profile=profile)
    task = mgr.ConfigureStorageDrsForPod_Task(pod=pod_ref, spec=spec, modify=True)
    return task._moId  # noqa: SLF001


# ---------------------------------------------------------------------------
# Per-VM SDRS overrides
# ---------------------------------------------------------------------------


def sdrs_vm_override_list(opts, pod, profile=None):
    pod_ref = _resolve_pod(opts, pod, profile=profile)
    out = []
    for entry in pod_ref.podStorageDrsEntry.storageDrsConfig.vmConfig or []:
        out.append(
            {
                "vm_moid": entry.vm._moId if entry.vm else None,  # noqa: SLF001
                "enabled": bool(getattr(entry, "enabled", True)),
                "behavior": str(entry.behavior) if entry.behavior else None,
                "intra_vm_affinity": bool(getattr(entry, "intraVmAffinity", True)),
            }
        )
    return out


def sdrs_vm_override_set(
    opts,
    pod,
    vm_moid,
    behavior=None,
    enabled=None,
    intra_vm_affinity=None,
    profile=None,
):
    """Add / replace the SDRS override for *vm_moid* on *pod*.

    *behavior*: ``manual`` | ``automated``.
    """
    pod_ref = _resolve_pod(opts, pod, profile=profile)
    info = vim.storageDrs.VmConfigInfo(vm=vim.VirtualMachine(vm_moid, None))
    if behavior is not None:
        info.behavior = behavior
    if enabled is not None:
        info.enabled = bool(enabled)
    if intra_vm_affinity is not None:
        info.intraVmAffinity = bool(intra_vm_affinity)
    spec = vim.storageDrs.ConfigSpec(
        vmConfigSpec=[vim.storageDrs.VmConfigSpec(operation="edit", info=info)]
    )
    mgr = _sdrs_mgr(opts, profile=profile)
    task = mgr.ConfigureStorageDrsForPod_Task(pod=pod_ref, spec=spec, modify=True)
    return task._moId  # noqa: SLF001


def sdrs_vm_override_remove(opts, pod, vm_moid, profile=None):
    pod_ref = _resolve_pod(opts, pod, profile=profile)
    spec = vim.storageDrs.ConfigSpec(
        vmConfigSpec=[
            vim.storageDrs.VmConfigSpec(
                operation="remove", removeKey=vim.VirtualMachine(vm_moid, None)
            )
        ]
    )
    mgr = _sdrs_mgr(opts, profile=profile)
    task = mgr.ConfigureStorageDrsForPod_Task(pod=pod_ref, spec=spec, modify=True)
    return task._moId  # noqa: SLF001
