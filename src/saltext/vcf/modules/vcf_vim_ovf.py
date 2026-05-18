"""Execution module for OVF export via ``OvfManager``."""

from saltext.vcf.clients import vim_ovf as c

__virtualname__ = "vcf_vim_ovf"


def __virtual__():
    return __virtualname__


def descriptor(vm, ovf_name=None, description="", profile=None):
    """Generate just the OVF descriptor XML for *vm* (no VMDK pull).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_ovf.descriptor <vm>

    """
    return c.descriptor(__opts__, vm, ovf_name=ovf_name, description=description, profile=profile)


def export(vm, output_dir, ovf_name=None, profile=None):
    """Export the full OVF bundle (descriptor + VMDKs) to *output_dir*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_ovf.export <vm> /tmp/ovf-out

    """
    return c.export(__opts__, vm, output_dir, ovf_name=ovf_name, profile=profile)
