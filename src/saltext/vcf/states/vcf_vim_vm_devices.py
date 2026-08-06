"""State module for niche VM virtual devices (vTPM, vGPU, serial)."""

from saltext.vcf.clients import vim_vm_devices as c

__virtualname__ = "vcf_vim_vm_devices"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def tpm_present(name, vm=None, profile=None):
    """Ensure a vTPM device is attached to *vm*. VM must be powered off."""
    vm = vm or name
    ret = _ret(name)
    existing = c.tpm_list(__opts__, vm, profile=profile)
    if existing:
        ret["comment"] = f"vTPM on {vm} already present"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"vTPM would be added to {vm}"
        return ret
    c.tpm_add(__opts__, vm, profile=profile)
    ret["changes"] = {"added": "vTPM"}
    ret["comment"] = f"vTPM added to {vm}"
    return ret


def tpm_absent(name, vm=None, profile=None):
    """Ensure no vTPM device on *vm*."""
    vm = vm or name
    ret = _ret(name)
    existing = c.tpm_list(__opts__, vm, profile=profile)
    if not existing:
        ret["comment"] = f"vTPM on {vm} already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"vTPM would be removed from {vm}"
        return ret
    c.tpm_remove(__opts__, vm, profile=profile)
    ret["changes"] = {"removed": "vTPM"}
    ret["comment"] = f"vTPM removed from {vm}"
    return ret


def vgpu_present(name, vm, profile_name, profile=None):
    """Ensure a vGPU with *profile_name* is attached to *vm*."""
    ret = _ret(name)
    existing = c.vgpu_list(__opts__, vm, profile=profile)
    if any(g.get("vgpu_profile") == profile_name for g in existing):
        ret["comment"] = f"vGPU {profile_name!r} already present on {vm}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"vGPU {profile_name!r} would be added to {vm}"
        return ret
    c.vgpu_add(__opts__, vm, profile_name, profile=profile)
    ret["changes"] = {"added": profile_name}
    ret["comment"] = f"vGPU {profile_name!r} added to {vm}"
    return ret


def vgpu_absent(name, vm, profile_name=None, profile=None):
    """Ensure no vGPU (or no vGPU with *profile_name*) on *vm*."""
    ret = _ret(name)
    existing = c.vgpu_list(__opts__, vm, profile=profile)
    targets = [g for g in existing if profile_name is None or g.get("vgpu_profile") == profile_name]
    if not targets:
        ret["comment"] = (
            f"vGPU{f' {profile_name!r}' if profile_name else ''} on {vm} already absent"
        )
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"vGPU would be removed from {vm}"
        return ret
    c.vgpu_remove(__opts__, vm, profile_name=profile_name, profile=profile)
    ret["changes"] = {"removed": profile_name or "all"}
    ret["comment"] = f"vGPU removed from {vm}"
    return ret


def serial_present(
    name, vm, backing="network", uri=None, file_path=None, direction="server", profile=None
):
    """Ensure a matching serial port exists on *vm*."""
    ret = _ret(name)
    existing = c.serial_list(__opts__, vm, profile=profile)
    for s in existing:
        if backing == "network" and s.get("uri") == uri:
            ret["comment"] = f"serial port {uri!r} on {vm} already present"
            return ret
        if backing == "file" and s.get("file") == file_path:
            ret["comment"] = f"serial port {file_path!r} on {vm} already present"
            return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"serial port would be added to {vm}"
        return ret
    c.serial_add(
        __opts__,
        vm,
        backing=backing,
        uri=uri,
        file_path=file_path,
        direction=direction,
        profile=profile,
    )
    ret["changes"] = {"added": uri or file_path}
    ret["comment"] = f"serial port added to {vm}"
    return ret


def usb_controllers_absent(name, connected_only=True, profile=None):
    """Ensure no VM in the inventory has a USB controller device (Broadcom KB 316384).

    Fleet-wide, not single-VM scoped: scans every VM, matching the KB's
    reference PowerCLI script's ``Get-VM | ? {... -match "USB"}`` sweep,
    then removes any USB controller found. Under ``test=True`` this only
    reports which VMs/devices would be touched — no reconfiguration is
    issued.

    When *connected_only* is true (default, matches the reference
    script), VMs that aren't in the ``connected`` runtime state are
    reported but not touched — a disconnected/orphaned VM's hardware
    can't be reconfigured anyway.
    """
    ret = _ret(name)
    found = c.list_vms_with_usb_controllers(__opts__, profile=profile)
    if connected_only:
        targets = [v for v in found if v["connected"]]
        skipped = [v for v in found if not v["connected"]]
    else:
        targets, skipped = found, []

    if not targets:
        comment = "no VMs with a USB controller found"
        if skipped:
            comment += f" ({len(skipped)} disconnected VM(s) with a USB controller were skipped)"
        ret["comment"] = comment
        return ret

    vm_names = [v["vm"] for v in targets]
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"USB controller(s) would be removed from: {', '.join(vm_names)}"
        ret["changes"] = {"would_remove": {v["vm"]: v["devices"] for v in targets}}
        return ret

    removed = {}
    errors = {}
    for v in targets:
        try:
            removed[v["vm"]] = c.usb_controllers_remove(__opts__, v["moid"], profile=profile)
        except Exception as exc:  # pylint: disable=broad-except
            errors[v["vm"]] = str(exc)

    ret["changes"] = {"removed": removed}
    if errors:
        ret["result"] = False
        ret["changes"]["errors"] = errors
        ret["comment"] = (
            f"removed USB controller(s) from {len(removed)} VM(s); failed on {len(errors)}"
        )
    else:
        ret["comment"] = (
            f"removed USB controller(s) from {len(removed)} VM(s): {', '.join(vm_names)}"
        )
    return ret
