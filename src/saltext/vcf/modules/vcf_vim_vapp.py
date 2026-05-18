"""Execution module for vSphere vApp containers."""

from saltext.vcf.clients import vim_vapp as c

__virtualname__ = "vcf_vim_vapp"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List every vApp in the inventory.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vapp.list_
    """
    return c.list_(__opts__, profile=profile)


def get(vapp, profile=None):
    """Return one vApp by name or moId.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vapp.get <vapp>
    """
    return c.get(__opts__, vapp, profile=profile)


def create(name, parent_resource_pool, annotation=None, profile=None):
    """Create a vApp under *parent_resource_pool*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vapp.create <name> <parent_resource_pool>
    """
    return c.create(__opts__, name, parent_resource_pool, annotation=annotation, profile=profile)


def power_on(vapp, profile=None):
    """Power on every VM in the vApp.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vapp.power_on <vapp>
    """
    return c.power_on(__opts__, vapp, profile=profile)


def power_off(vapp, force=False, profile=None):
    """Power off every VM in the vApp.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vapp.power_off <vapp>
    """
    return c.power_off(__opts__, vapp, force=force, profile=profile)


def suspend(vapp, profile=None):
    """Suspend the vApp.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vapp.suspend <vapp>
    """
    return c.suspend(__opts__, vapp, profile=profile)


def delete(vapp, profile=None):
    """Destroy the vApp.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vapp.delete <vapp>
    """
    return c.delete(__opts__, vapp, profile=profile)


def update(vapp, annotation=None, profile=None):
    """Update vApp metadata.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vapp.update <vapp> annotation='new annotation'
    """
    return c.update(__opts__, vapp, annotation=annotation, profile=profile)
