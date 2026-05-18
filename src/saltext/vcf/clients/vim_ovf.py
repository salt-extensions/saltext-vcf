"""Export OVF descriptors via ``OvfManager`` + ``HttpNfcLease``.

Import is intentionally not wrapped here — content library OVF deploy
(`vcenter_content_library.ovf_deploy`) is the modern path for that workflow.
"""

from pathlib import Path

import requests
from pyVmomi import vim

from saltext.vcf.utils import vcenter as vc_rest
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


def descriptor(opts, vm_id_or_name, *, ovf_name=None, description="", profile=None):
    """Generate and return the OVF descriptor XML for *vm_id_or_name*.

    Does NOT export VMDKs — use :func:`export` for the full bundle.
    """
    vm = _find_vm(opts, vm_id_or_name, profile=profile)
    ovf_mgr = soap.content(opts, profile=profile).ovfManager
    spec = vim.OvfManager.CreateDescriptorParams()
    spec.name = ovf_name or vm.name
    spec.description = description
    result = ovf_mgr.CreateDescriptor(obj=vm, cdp=spec)
    return {"ovf": result.ovfDescriptor, "warnings": list(result.warning or [])}


def export(opts, vm_id_or_name, output_dir, *, ovf_name=None, profile=None):
    """Export OVF descriptor + all VMDKs to *output_dir*.

    Returns ``{descriptor_path, vmdk_paths}``. The lease must be released
    (``Complete()``) when the pull finishes, which this function does for you.
    """
    vm = _find_vm(opts, vm_id_or_name, profile=profile)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    cfg = vc_rest.get_config(opts, profile=profile)
    cookie = soap.session_cookie(opts, profile=profile)
    headers = {"Cookie": cookie}

    lease = vm.ExportVm()
    # Wait for lease to become ready.
    while lease.state == vim.HttpNfcLease.State.initializing:
        pass
    if lease.state == vim.HttpNfcLease.State.error:
        raise RuntimeError(lease.error.msg if lease.error else "lease error")

    try:
        vmdk_paths = []
        for device in lease.info.deviceUrl or []:
            if not device.disk:
                continue
            target = out / f"{vm.name}-{device.targetId}.vmdk"
            with requests.get(
                device.url,
                headers=headers,
                stream=True,
                verify=cfg["verify_ssl"],
                timeout=3600,
            ) as resp:
                resp.raise_for_status()
                with open(target, "wb") as fp:
                    for chunk in resp.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            fp.write(chunk)
            vmdk_paths.append(str(target))

        ovf_mgr = soap.content(opts, profile=profile).ovfManager
        spec = vim.OvfManager.CreateDescriptorParams()
        spec.name = ovf_name or vm.name
        spec.ovfFiles = [
            vim.OvfManager.OvfFile(
                deviceId=device.key,
                path=Path(vmdk_paths[i]).name,
                size=Path(vmdk_paths[i]).stat().st_size,
            )
            for i, device in enumerate(d for d in lease.info.deviceUrl or [] if d.disk)
        ]
        descriptor_obj = ovf_mgr.CreateDescriptor(obj=vm, cdp=spec)
        descriptor_path = out / f"{vm.name}.ovf"
        descriptor_path.write_text(descriptor_obj.ovfDescriptor)
    finally:
        lease.HttpNfcLeaseComplete()

    return {
        "descriptor_path": str(descriptor_path),
        "vmdk_paths": vmdk_paths,
    }
