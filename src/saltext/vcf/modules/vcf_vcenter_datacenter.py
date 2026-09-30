"""Execution module for vCenter datacenters."""

from saltext.vcf.clients import vcenter_datacenter as r

__virtualname__ = "vcf_vcenter_datacenter"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List datacenters known to vCenter.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_datacenter.list_

    """
    return r.list_(__opts__, profile=profile)


def get(datacenter, profile=None):
    """Return details for a single datacenter by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_datacenter.get <datacenter>

    """
    return r.get(__opts__, datacenter, profile=profile)


def create(name, folder=None, profile=None):
    """Create a datacenter.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_datacenter.create <name> <folder>

    """
    return r.create(__opts__, name, folder=folder, profile=profile)


def delete(datacenter, profile=None):
    """Delete a datacenter by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_datacenter.delete <datacenter>

    """
    return r.delete(__opts__, datacenter, profile=profile)


def get_by_name(name, profile=None):
    """Return details for a single datacenter by name.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_datacenter.get_by_name dc-01
    """
    return r.get_by_name(__opts__, name, profile=profile)


def detail(name, profile=None):
    """Return datacenter details plus per-type folder lists (vm/folder parity).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_datacenter.detail dc-01
    """
    import saltext.vcf.clients.vcenter_folder as folder_c  # noqa: PLC0415

    dc = r.get_by_name(__opts__, name, profile=profile)
    dc_id = dc["datacenter"] if isinstance(dc, dict) and "datacenter" in dc else dc
    out = dict(dc) if isinstance(dc, dict) else {"datacenter": dc}
    for label, ftype in (
        ("vm_folders", "VIRTUAL_MACHINE"),
        ("ds_folders", "DATASTORE"),
        ("hst_folders", "HOST"),
        ("ntwk_folders", "NETWORK"),
    ):
        folders = folder_c.list_by_type(__opts__, ftype, profile=profile) or []
        out[label] = [f["folder"] for f in folders if f.get("datacenter") == dc_id]
    return out
