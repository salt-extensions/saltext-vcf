"""VM snapshots via pyVmomi SOAP (vCenter REST has no snapshot surface in 9.2).

Probed against VCF 9.2: ``GET /api/vcenter/vm/{id}/snapshots`` returns 404.
This module uses ``vim.VirtualMachine.CreateSnapshot_Task`` and friends
through the SOAP service to author and manage snapshots.
"""

from pyVmomi import vim

from saltext.vmware.utils import vim as soap


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
    profile=None,
):
    """Create a snapshot, return the ``vim.Task`` moId."""
    vm = _find_vm(opts, vm_id_or_name, profile=profile)
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
