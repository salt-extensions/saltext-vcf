"""State module for niche VM virtual devices (vTPM, vGPU, serial)."""

from saltext.vmware.clients import vim_vm_devices as c

__virtualname__ = "vmware_vim_vm_devices"


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
