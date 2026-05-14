"""Execution module for VM clone + create + reconfigure (SOAP)."""

from saltext.vmware.clients import vim_vm as c

__virtualname__ = "vmware_vim_vm"


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

        salt '*' vmware_vim_vm.clone tmpl-rhel9 web-01 folder=group-v3 datastore=datastore-13 cluster=domain-c9 power_on=true
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

        salt '*' vmware_vim_vm.create blank-vm group-v3 datastore-13 cluster=domain-c9 cpu_count=2 memory_mb=4096
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

        salt '*' vmware_vim_vm.reconfigure vm-100 cpu_count=4 memory_mb=8192
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

        salt '*' vmware_vim_vm.get_advanced_settings vm-100
    """
    return c.get_advanced_settings(__opts__, vm, profile=profile)


def destroy(vm, profile=None):
    """Power off (if needed) and destroy the VM.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm.destroy vm-100
    """
    return c.destroy(__opts__, vm, profile=profile)


def mark_as_template(vm, profile=None):
    """Convert a VM into a template.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm.mark_as_template vm-100
    """
    return c.mark_as_template(__opts__, vm, profile=profile)


def mark_as_virtual_machine(template, resource_pool, host=None, profile=None):
    """Convert a template back into a VM.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm.mark_as_virtual_machine tmpl-rhel9 resgroup-c9
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

        salt '*' vmware_vim_vm.instant_clone <source> <name>
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

        salt '*' vmware_vim_vm.move_to_folder <vm> <folder>
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

        salt '*' vmware_vim_vm.register '[ds1] vm/vm.vmx' <name> <folder> cluster=<cluster>
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


def unregister(vm, profile=None):
    """Remove a VM from inventory without deleting its files.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm.unregister <vm>
    """
    return c.unregister(__opts__, vm, profile=profile)
