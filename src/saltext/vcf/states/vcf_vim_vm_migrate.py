"""State module for VM relocation (``vmware_vm.relocate`` parity)."""

from saltext.vcf.clients import vim_vm_migrate as c
from saltext.vcf.clients import vim_vm as vm_c

__virtualname__ = "vcf_vim_vm_migrate"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def relocate(name, new_host_name=None, datastore_name=None, profile=None):
    """Relocate VM *name* to *new_host_name* and/or *datastore_name*.

    Detects "already there" by comparing the VM's current host name and
    attached datastore names (via :func:`vcf_vim_vm.runtime`).

    .. code-block:: yaml

        Relocate VM:
          vcf_vim_vm_migrate.relocate:
            - name: vm-100
            - new_host_name: host1
            - datastore_name: ds1
    """
    ret = _ret(name)
    current = vm_c.runtime(__opts__, name, profile=profile)
    host_ok = new_host_name is None or current.get("host") == new_host_name
    ds_ok = (
        datastore_name is None
        or datastore_name in (current.get("datastores") or [])
    )
    if host_ok and ds_ok:
        ret["comment"] = f"VM {name!r} is already on host {new_host_name} / datastore {datastore_name}."
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"VM {name!r} would be relocated to host {new_host_name} / datastore {datastore_name}."
        ret["changes"] = {"host": (current.get("host"), new_host_name)}
        return ret
    c.relocate(
        __opts__,
        name,
        host=new_host_name,
        datastore=datastore_name,
        profile=profile,
    )
    ret["changes"] = {
        "host": (current.get("host"), new_host_name),
        "datastore": (current.get("datastores"), datastore_name),
    }
    ret["comment"] = f"VM {name!r} relocation submitted."
    return ret
