"""Execution module for First-Class Disks (FCD / Improved Virtual Disks)."""

from saltext.vmware.clients import vim_first_class_disk as c

__virtualname__ = "vmware_vim_first_class_disk"


def __virtual__():
    return __virtualname__


def list_(datastore, profile=None):
    """List FCDs on *datastore*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_first_class_disk.list_ <datastore>

    """
    return c.list_(__opts__, datastore, profile=profile)


def get(vstorage_object_id, datastore, profile=None):
    """Return one FCD by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_first_class_disk.get <vstorage_object_id> <datastore>

    """
    return c.get(__opts__, vstorage_object_id, datastore, profile=profile)


def create(
    name,
    datastore,
    capacity_gb,
    provisioning="thin",
    profile_id=None,
    keep_after_delete_vm=False,
    profile=None,
):
    """Create a new FCD.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_first_class_disk.create my-disk <datastore> 10

    """
    return c.create(
        __opts__,
        name,
        datastore,
        capacity_gb,
        provisioning=provisioning,
        profile_id=profile_id,
        keep_after_delete_vm=keep_after_delete_vm,
        profile=profile,
    )


def delete(vstorage_object_id, datastore, profile=None):
    """Delete an FCD.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_first_class_disk.delete <vstorage_object_id> <datastore>

    """
    return c.delete(__opts__, vstorage_object_id, datastore, profile=profile)


def rename(vstorage_object_id, datastore, new_name, profile=None):
    """Rename an FCD.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_first_class_disk.rename <vstorage_object_id> <datastore> <new_name>

    """
    return c.rename(__opts__, vstorage_object_id, datastore, new_name, profile=profile)


def extend(vstorage_object_id, datastore, new_capacity_gb, profile=None):
    """Grow an FCD to *new_capacity_gb*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_first_class_disk.extend <vstorage_object_id> <datastore> 20

    """
    return c.extend(__opts__, vstorage_object_id, datastore, new_capacity_gb, profile=profile)


def register(datastore, path, name, profile=None):
    """Register an existing VMDK as an FCD.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_first_class_disk.register <datastore> <path> <name>

    """
    return c.register(__opts__, datastore, path, name, profile=profile)


def set_keep_after_delete_vm(vstorage_object_id, datastore, keep, profile=None):
    """Set the keepAfterDeleteVm flag on an FCD.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_first_class_disk.set_keep_after_delete_vm <id> <datastore> True

    """
    return c.set_keep_after_delete_vm(
        __opts__, vstorage_object_id, datastore, keep, profile=profile
    )


def attach_to_vm(
    vm,
    vstorage_object_id,
    datastore,
    controller_key=None,
    unit_number=None,
    profile=None,
):
    """Attach an FCD to *vm*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_first_class_disk.attach_to_vm <vm> <id> <datastore>

    """
    return c.attach_to_vm(
        __opts__,
        vm,
        vstorage_object_id,
        datastore,
        controller_key=controller_key,
        unit_number=unit_number,
        profile=profile,
    )


def detach_from_vm(vm, vstorage_object_id, profile=None):
    """Detach an FCD from *vm*.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_first_class_disk.detach_from_vm <vm> <id>

    """
    return c.detach_from_vm(__opts__, vm, vstorage_object_id, profile=profile)
