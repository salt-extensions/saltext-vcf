"""State module for VM snapshots (``vmware_vm.snapshot_present/absent`` parity)."""

from saltext.vcf.clients import vim_vm_snapshot as c

__virtualname__ = "vcf_vim_vm_snapshot"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(
    name,
    snapshot_name,
    description="",
    include_memory=False,
    quiesce=False,
    profile=None,
):
    """Ensure snapshot *snapshot_name* exists on VM *name*.

    .. code-block:: yaml

        VM snapshot present:
          vcf_vim_vm_snapshot.present:
            - name: vm-100
            - snapshot_name: pre-patch
            - description: before patching
            - include_memory: true
            - quiesce: true
    """
    ret = _ret(name)
    state = c.state(__opts__, name, snapshot_name, profile=profile)
    if state.get("present"):
        ret["comment"] = f"Snapshot {snapshot_name!r} already present on VM {name!r}."
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Snapshot {snapshot_name!r} would be created on VM {name!r}."
        ret["changes"] = {"new": snapshot_name}
        return ret
    c.create(
        __opts__,
        name,
        snapshot_name,
        description=description,
        memory=include_memory,
        quiesce=quiesce,
        profile=profile,
    )
    ret["changes"] = {"new": snapshot_name}
    ret["comment"] = f"Snapshot {snapshot_name!r} created on VM {name!r}."
    return ret


def absent(
    name,
    snapshot_name,
    snapshot_id=None,
    remove_children=False,
    profile=None,
):
    """Ensure snapshot *snapshot_name* does not exist on VM *name*.

    .. code-block:: yaml

        VM snapshot absent:
          vcf_vim_vm_snapshot.absent:
            - name: vm-100
            - snapshot_name: pre-patch
            - remove_children: true
    """
    ret = _ret(name)
    state = c.state(__opts__, name, snapshot_name, profile=profile)
    if not state.get("present"):
        ret["comment"] = f"Snapshot {snapshot_name!r} already absent on VM {name!r}."
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Snapshot {snapshot_name!r} would be removed from VM {name!r}."
        ret["changes"] = {"old": snapshot_name}
        return ret
    c.remove(
        __opts__,
        name,
        snapshot_name,
        remove_children=remove_children,
        profile=profile,
    )
    ret["changes"] = {"old": snapshot_name}
    ret["comment"] = f"Snapshot {snapshot_name!r} removed from VM {name!r}."
    return ret
