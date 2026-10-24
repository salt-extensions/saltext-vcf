"""Execution module for VM clone + create + reconfigure (SOAP)."""

from saltext.vcf.clients import vim_vm as c

__virtualname__ = "vcf_vim_vm"


def __virtual__():
    return __virtualname__


def clone(
    source,
    name,
    folder=None,
    datastore=None,
    host=None,
    resource_pool=None,
    cluster=None,
    template=False,
    power_on=False,
    cpu_count=None,
    memory_mb=None,
    annotation=None,
    profile=None,
):
    """Clone *source* VM/template into a new VM named *name*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm.clone tmpl-rhel9 web-01 folder=group-v3 datastore=datastore-13 cluster=domain-c9 power_on=true
    """
    return c.clone(
        __opts__,
        source,
        name,
        folder=folder,
        datastore=datastore,
        host=host,
        resource_pool=resource_pool,
        cluster=cluster,
        template=template,
        power_on=power_on,
        cpu_count=cpu_count,
        memory_mb=memory_mb,
        annotation=annotation,
        profile=profile,
    )


def create(
    name,
    folder,
    datastore,
    cpu_count=1,
    memory_mb=1024,
    guest_id="otherGuest64",
    cluster=None,
    host=None,
    resource_pool=None,
    annotation="",
    profile=None,
):
    """Create a bare VM (no disks, no NICs).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm.create blank-vm group-v3 datastore-13 cluster=domain-c9 cpu_count=2 memory_mb=4096
    """
    return c.create(
        __opts__,
        name,
        folder,
        datastore,
        cpu_count=cpu_count,
        memory_mb=memory_mb,
        guest_id=guest_id,
        cluster=cluster,
        host=host,
        resource_pool=resource_pool,
        annotation=annotation,
        profile=profile,
    )


def reconfigure(
    vm,
    cpu_count=None,
    cores_per_socket=None,
    memory_mb=None,
    annotation=None,
    advanced_settings=None,
    profile=None,
):
    """Adjust VM hardware/metadata. Only non-None fields are touched.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm.reconfigure vm-100 cpu_count=4 memory_mb=8192
    """
    return c.reconfigure(
        __opts__,
        vm,
        cpu_count=cpu_count,
        cores_per_socket=cores_per_socket,
        memory_mb=memory_mb,
        annotation=annotation,
        advanced_settings=advanced_settings,
        profile=profile,
    )


def get_advanced_settings(vm, profile=None):
    """Return VM ``extraConfig`` as a flat dict.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm.get_advanced_settings vm-100
    """
    return c.get_advanced_settings(__opts__, vm, profile=profile)


def get_resource_config(vm, profile=None):
    """Return VM CPU affinity/shares + memory reservation/lock snapshot.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm.get_resource_config vm-100
    """
    return c.get_resource_config(__opts__, vm, profile=profile)


def set_resource_config(
    vm,
    cpu_affinity=None,
    cpu_shares_level=None,
    cpu_shares=None,
    memory_reservation_mb=None,
    memory_reservation_locked_to_max=None,
    profile=None,
):
    """Set VM CPU affinity/shares + memory reservation/lock.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm.set_resource_config vm-100 cpu_affinity='[]' memory_reservation_mb=0
    """
    return c.set_resource_config(
        __opts__,
        vm,
        cpu_affinity=cpu_affinity,
        cpu_shares_level=cpu_shares_level,
        cpu_shares=cpu_shares,
        memory_reservation_mb=memory_reservation_mb,
        memory_reservation_locked_to_max=memory_reservation_locked_to_max,
        profile=profile,
    )


def destroy(vm, profile=None):
    """Power off (if needed) and destroy the VM.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm.destroy vm-100
    """
    return c.destroy(__opts__, vm, profile=profile)


def mark_as_template(vm, profile=None):
    """Convert a VM into a template.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm.mark_as_template vm-100
    """
    return c.mark_as_template(__opts__, vm, profile=profile)


def mark_as_virtual_machine(template, resource_pool, host=None, profile=None):
    """Convert a template back into a VM.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm.mark_as_virtual_machine tmpl-rhel9 resgroup-c9
    """
    return c.mark_as_virtual_machine(__opts__, template, resource_pool, host=host, profile=profile)


def instant_clone(
    source,
    name,
    folder=None,
    datastore=None,
    host=None,
    resource_pool=None,
    extra_config=None,
    profile=None,
):
    """Instant-clone a running *source* VM into a new VM named *name*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm.instant_clone <source> <name>
    """
    return c.instant_clone(
        __opts__,
        source,
        name,
        folder=folder,
        datastore=datastore,
        host=host,
        resource_pool=resource_pool,
        extra_config=extra_config,
        profile=profile,
    )


def move_to_folder(vm, folder, profile=None):
    """Reparent *vm* under *folder*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm.move_to_folder <vm> <folder>
    """
    return c.move_to_folder(__opts__, vm, folder, profile=profile)


def register(
    vmx_path,
    name,
    folder,
    resource_pool=None,
    cluster=None,
    host=None,
    as_template=False,
    profile=None,
):
    """Register an existing .vmx file as a new VM in inventory.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm.register '[ds1] vm/vm.vmx' <name> <folder> cluster=<cluster>
    """
    return c.register(
        __opts__,
        vmx_path,
        name,
        folder,
        resource_pool=resource_pool,
        cluster=cluster,
        host=host,
        as_template=as_template,
        profile=profile,
    )


def unregister(vm, shutdown=False, profile=None):
    """Remove a VM from inventory without deleting its files.

    With ``shutdown=True`` a running VM is gracefully shut down via
    VMware Tools first; with ``shutdown=False`` the VM must already be
    powered off.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm.unregister <vm> shutdown=true
    """
    return c.unregister(__opts__, vm, shutdown=shutdown, profile=profile)


def list_templates(profile=None):
    """List the names of every VM flagged as a template.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm.list_templates
    """
    return c.list_templates(__opts__, profile=profile)


def path(vm, profile=None):
    """Return the inventory path of *vm* from the root folder down.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm.path vm-100
    """
    return c.path(__opts__, vm, profile=profile)


def runtime(vm, profile=None):
    """Return the VM's current host and attached datastore names.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm.runtime vm-100
    """
    return c.runtime(__opts__, vm, profile=profile)


def info(vm, profile=None):
    """Return a composed per-VM detail dict (guest IPs, MACs, uuid, paths).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm.info vm-100
    """
    return c.info(__opts__, vm, profile=profile)


def register_all(
    datastore,
    resource_pool=None,
    cluster=None,
    host=None,
    folder=None,
    profile=None,
):
    """Register every ``*.vmx`` file found on *datastore*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm.register_all ds1 cluster=domain-c9 folder=restored
    """
    return c.register_all(
        __opts__,
        datastore,
        resource_pool=resource_pool,
        cluster=cluster,
        host=host,
        folder=folder,
        profile=profile,
    )


def unregister_all(folder=None, shutdown=False, profile=None):
    """Unregister every VM under *folder* (or the whole inventory).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm.unregister_all folder=restored shutdown=true
    """
    return c.unregister_all(__opts__, folder, shutdown=shutdown, profile=profile)
