"""VM snapshots via pyVmomi SOAP (vCenter REST has no snapshot surface in 9.2).

Probed against VCF 9.2: ``GET /api/vcenter/vm/{id}/snapshots`` returns 404.
This module uses ``vim.VirtualMachine.CreateSnapshot_Task`` and friends
through the SOAP service to author and manage snapshots.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _find_vm(opts, vm_id_or_name, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.VirtualMachine], True
    )
    try:
        for vm in container.view:
            if vm_id_or_name in (vm._moId, vm.name):  # noqa: SLF001
                return vm
    finally:
        container.Destroy()
    raise LookupError(f"VM {vm_id_or_name!r} not found")


def list_(opts, vm_id_or_name, profile=None):
    """Return a tree of snapshots: ``[{"id", "name", "description", "children": [...]}]``."""
    vm = _find_vm(opts, vm_id_or_name, profile=profile)
    if not vm.snapshot:
        return []
    return [_tree(node) for node in vm.snapshot.rootSnapshotList]


def current(opts, vm_id_or_name, profile=None):
    """Return the current (active) snapshot dict, or None."""
    vm = _find_vm(opts, vm_id_or_name, profile=profile)
    if not vm.snapshot or not vm.snapshot.currentSnapshot:
        return None
    cur = vm.snapshot.currentSnapshot
    return {
        "id": cur._moId,
        "name": _find_name_in_tree(vm.snapshot.rootSnapshotList, cur._moId),
    }


def create(
    opts,
    vm_id_or_name,
    name,
    *,
    description="",
    memory=False,
    quiesce=False,
    vss_options=None,
    profile=None,
):
    """Create a snapshot, return the ``vim.Task`` moId.

    *vss_options* — optional dict for Windows-guest VSS quiesce. Supported keys:
    ``vss_backup_type`` (1=full, 2=incremental, 5=differential, 6=log),
    ``vss_backup_context`` (e.g. ``backup_context_backup``),
    ``vss_partial_file_support`` (bool),
    ``vss_bootable_system_state`` (bool),
    ``timeout`` (seconds).
    Setting any value implies ``quiesce=True`` and uses
    ``CreateSnapshotEx_Task`` with a WindowsQuiesceSpec.
    """
    vm = _find_vm(opts, vm_id_or_name, profile=profile)
    if vss_options:
        spec = vim.vm.WindowsQuiesceSpec()
        if "timeout" in vss_options:
            spec.timeout = int(vss_options["timeout"])
        if "vss_backup_type" in vss_options:
            spec.vssBackupType = int(vss_options["vss_backup_type"])
        if "vss_backup_context" in vss_options:
            spec.vssBackupContext = vss_options["vss_backup_context"]
        if "vss_partial_file_support" in vss_options:
            spec.vssPartialFileSupport = bool(vss_options["vss_partial_file_support"])
        if "vss_bootable_system_state" in vss_options:
            spec.vssBootableSystemState = bool(vss_options["vss_bootable_system_state"])
        task = vm.CreateSnapshotEx_Task(
            name=name,
            description=description,
            memory=bool(memory),
            quiesceSpec=spec,
        )
    else:
        task = vm.CreateSnapshot_Task(
            name=name, description=description, memory=bool(memory), quiesce=bool(quiesce)
        )
    return task._moId  # noqa: SLF001


def revert(opts, vm_id_or_name, snapshot_name, *, suppress_power_on=False, profile=None):
    """Revert to a named snapshot. Returns vim.Task moId."""
    vm = _find_vm(opts, vm_id_or_name, profile=profile)
    snap = _find_snap_by_name(vm.snapshot.rootSnapshotList, snapshot_name) if vm.snapshot else None
    if snap is None:
        raise LookupError(f"snapshot {snapshot_name!r} not found on {vm.name}")
    task = snap.snapshot.RevertToSnapshot_Task(suppressPowerOn=bool(suppress_power_on))
    return task._moId  # noqa: SLF001


def remove(opts, vm_id_or_name, snapshot_name, *, remove_children=False, profile=None):
    """Delete a snapshot by name. Returns vim.Task moId."""
    vm = _find_vm(opts, vm_id_or_name, profile=profile)
    snap = _find_snap_by_name(vm.snapshot.rootSnapshotList, snapshot_name) if vm.snapshot else None
    if snap is None:
        raise LookupError(f"snapshot {snapshot_name!r} not found on {vm.name}")
    task = snap.snapshot.RemoveSnapshot_Task(removeChildren=bool(remove_children))
    return task._moId  # noqa: SLF001


def remove_all(opts, vm_id_or_name, profile=None):
    """Delete every snapshot on the VM. Returns vim.Task moId."""
    vm = _find_vm(opts, vm_id_or_name, profile=profile)
    task = vm.RemoveAllSnapshots_Task()
    return task._moId  # noqa: SLF001


def consolidate(opts, vm_id_or_name, profile=None):
    """Consolidate VM disks (merge orphaned snapshot deltas). Returns vim.Task moId."""
    vm = _find_vm(opts, vm_id_or_name, profile=profile)
    task = vm.ConsolidateVMDisks_Task()
    return task._moId  # noqa: SLF001


def state(opts, vm_id_or_name, snapshot_name, profile=None):
    """Return ``{present, is_current, has_memory, has_quiesce, children}`` for one named snapshot.

    Returns ``{"present": False}`` if the named snapshot does not exist.
    """
    vm = _find_vm(opts, vm_id_or_name, profile=profile)
    if not vm.snapshot:
        return {"present": False}
    node = _find_snap_by_name(vm.snapshot.rootSnapshotList, snapshot_name)
    if node is None:
        return {"present": False}
    current_id = (
        vm.snapshot.currentSnapshot._moId if vm.snapshot.currentSnapshot else None  # noqa: SLF001
    )
    snap_id = node.snapshot._moId  # noqa: SLF001
    return {
        "present": True,
        "id": snap_id,
        "is_current": snap_id == current_id,
        "has_memory": bool(getattr(node, "backupManifest", None))
        or bool(getattr(node, "vmsd", None)),  # heuristic; pyVmomi exposes via state metadata
        "has_quiesce": bool(getattr(node, "quiesced", False)),
        "state": str(node.state) if getattr(node, "state", None) else None,
        "children": [child.name for child in (node.childSnapshotList or [])],
    }


# ---------------------------------------------------------------------------
# Tree helpers
# ---------------------------------------------------------------------------


def _tree(node):
    return {
        "id": node.snapshot._moId,  # noqa: SLF001
        "name": node.name,
        "description": node.description,
        "create_time": node.createTime.isoformat() if node.createTime else None,
        "state": str(node.state),
        "quiesced": bool(getattr(node, "quiesced", False)),
        "children": [_tree(child) for child in (node.childSnapshotList or [])],
    }


def _find_snap_by_name(tree, name):
    for node in tree or []:
        if node.name == name:
            return node
        found = _find_snap_by_name(node.childSnapshotList, name)
        if found is not None:
            return found
    return None


def _find_name_in_tree(tree, snap_id):
    for node in tree or []:
        if node.snapshot._moId == snap_id:  # noqa: SLF001
            return node.name
        found = _find_name_in_tree(node.childSnapshotList, snap_id)
        if found is not None:
            return found
    return None
