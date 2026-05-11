"""VM clone + create + reconfigure via SOAP.

REST (``/api/vcenter/vm``) covers basic VM lifecycle but lacks the
hardware-customization depth Terraform users expect (clone from
template with full vCPU/memory/disk/network override, guest OS
customization specs, etc.). This module exposes the SOAP path:

- ``vim.VirtualMachine.CloneVM_Task`` for template/source clones
- ``vim.Folder.CreateVM_Task`` for from-scratch VMs
- ``vim.VirtualMachine.ReconfigVM_Task`` for hardware-level edits

Disk/NIC management has its own dedicated modules (``vim_vm_disk`` and
``vim_vm_nic``) since each has a richer surface.
"""

from pyVmomi import vim

from saltext.vmware.utils import vim as soap

# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------


def _vm(opts, vm_id_or_name, profile=None):
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


def _find_by_type(opts, vim_type, name_or_id, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim_type], True)
    try:
        for entity in container.view:
            if name_or_id in (entity._moId, entity.name):  # noqa: SLF001
                return entity
    finally:
        container.Destroy()
    raise LookupError(f"{vim_type.__name__} {name_or_id!r} not found")


# ---------------------------------------------------------------------------
# Clone
# ---------------------------------------------------------------------------


def clone(
    opts,
    source,
    name,
    *,
    folder=None,
    datastore=None,
    host=None,
    resource_pool=None,
    cluster=None,
    template=False,
    power_on=False,
    customization=None,
    cpu_count=None,
    memory_mb=None,
    annotation=None,
    profile=None,
):
    """Clone *source* (VM or template) into a new VM named *name*.

    All target placement fields accept either an MoID or a name. *folder*
    and *datastore* are required; *resource_pool* defaults to the root pool
    on *cluster* (or *host*) when omitted.
    """
    src = _vm(opts, source, profile=profile)
    target_folder = _find_by_type(opts, vim.Folder, folder, profile=profile)
    target_datastore = _find_by_type(opts, vim.Datastore, datastore, profile=profile)

    relocate = vim.vm.RelocateSpec(datastore=target_datastore)
    if host:
        relocate.host = _find_by_type(opts, vim.HostSystem, host, profile=profile)
    if resource_pool:
        relocate.pool = _find_by_type(opts, vim.ResourcePool, resource_pool, profile=profile)
    elif cluster:
        cluster_obj = _find_by_type(opts, vim.ClusterComputeResource, cluster, profile=profile)
        relocate.pool = cluster_obj.resourcePool

    spec = vim.vm.CloneSpec(
        location=relocate,
        powerOn=bool(power_on),
        template=bool(template),
    )

    if any(v is not None for v in (cpu_count, memory_mb, annotation)):
        config = vim.vm.ConfigSpec()
        if cpu_count is not None:
            config.numCPUs = int(cpu_count)
        if memory_mb is not None:
            config.memoryMB = int(memory_mb)
        if annotation is not None:
            config.annotation = annotation
        spec.config = config

    if customization is not None:
        spec.customization = customization

    task = src.CloneVM_Task(folder=target_folder, name=name, spec=spec)
    return task._moId  # noqa: SLF001


# ---------------------------------------------------------------------------
# Create-from-scratch
# ---------------------------------------------------------------------------


def create(
    opts,
    name,
    folder,
    datastore,
    *,
    cpu_count=1,
    memory_mb=1024,
    guest_id="otherGuest64",
    cluster=None,
    host=None,
    resource_pool=None,
    annotation="",
    profile=None,
):
    """Create a bare VM (no disks, no NICs)."""
    target_folder = _find_by_type(opts, vim.Folder, folder, profile=profile)
    target_datastore = _find_by_type(opts, vim.Datastore, datastore, profile=profile)

    if resource_pool:
        pool = _find_by_type(opts, vim.ResourcePool, resource_pool, profile=profile)
    elif cluster:
        cluster_obj = _find_by_type(opts, vim.ClusterComputeResource, cluster, profile=profile)
        pool = cluster_obj.resourcePool
    elif host:
        host_obj = _find_by_type(opts, vim.HostSystem, host, profile=profile)
        pool = host_obj.parent.resourcePool
    else:
        raise ValueError("provide cluster, host, or resource_pool for VM placement")

    host_obj = _find_by_type(opts, vim.HostSystem, host, profile=profile) if host else None

    config = vim.vm.ConfigSpec(
        name=name,
        memoryMB=int(memory_mb),
        numCPUs=int(cpu_count),
        guestId=guest_id,
        annotation=annotation,
        files=vim.vm.FileInfo(vmPathName=f"[{target_datastore.name}]"),
    )
    task = target_folder.CreateVM_Task(config=config, pool=pool, host=host_obj)
    return task._moId  # noqa: SLF001


# ---------------------------------------------------------------------------
# Reconfigure (hardware + metadata)
# ---------------------------------------------------------------------------


def reconfigure(
    opts,
    vm_id_or_name,
    *,
    cpu_count=None,
    cores_per_socket=None,
    memory_mb=None,
    annotation=None,
    advanced_settings=None,
    profile=None,
):
    """Adjust VM hardware/metadata. Only non-None fields are touched."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    config = vim.vm.ConfigSpec()
    if cpu_count is not None:
        config.numCPUs = int(cpu_count)
    if cores_per_socket is not None:
        config.numCoresPerSocket = int(cores_per_socket)
    if memory_mb is not None:
        config.memoryMB = int(memory_mb)
    if annotation is not None:
        config.annotation = annotation
    if advanced_settings:
        config.extraConfig = [
            vim.option.OptionValue(key=k, value=v) for k, v in advanced_settings.items()
        ]
    task = vm.ReconfigVM_Task(spec=config)
    return task._moId  # noqa: SLF001


def get_advanced_settings(opts, vm_id_or_name, profile=None):
    """Return the VM's ``extraConfig`` as a flat ``{key: value}`` dict."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    return {opt.key: opt.value for opt in (vm.config.extraConfig or [])}


# ---------------------------------------------------------------------------
# Destroy
# ---------------------------------------------------------------------------


def destroy(opts, vm_id_or_name, profile=None):
    """Power off (if needed) and destroy the VM. Returns task moId."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    if vm.runtime.powerState == "poweredOn":
        vm.PowerOffVM_Task()
    task = vm.Destroy_Task()
    return task._moId  # noqa: SLF001


def mark_as_template(opts, vm_id_or_name, profile=None):
    vm = _vm(opts, vm_id_or_name, profile=profile)
    vm.MarkAsTemplate()


def mark_as_virtual_machine(opts, template_id_or_name, resource_pool, host=None, profile=None):
    template = _vm(opts, template_id_or_name, profile=profile)
    pool = _find_by_type(opts, vim.ResourcePool, resource_pool, profile=profile)
    host_obj = _find_by_type(opts, vim.HostSystem, host, profile=profile) if host else None
    template.MarkAsVirtualMachine(pool=pool, host=host_obj)
