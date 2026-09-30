"""State module for datastore maintenance mode (``vmware_datastore.maintenance_mode`` parity)."""

from saltext.vcf.clients import vim_datastore as c

__virtualname__ = "vcf_vim_datastore"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def maintenance_mode(name, enter_maintenance_mode=True, profile=None):
    """Ensure the datastore *name* is in (or out of) maintenance mode.

    .. code-block:: yaml

        Datastore maintenance:
          vcf_vim_datastore.maintenance_mode:
            - name: ds1
            - enter_maintenance_mode: true
    """
    ret = _ret(name)
    current = c.get_or_none(__opts__, name, profile=profile)
    if current is None:
        ret["result"] = False
        ret["comment"] = f"datastore {name!r} not found"
        return ret
    in_mm = current["maintenance_mode"] == "inMaintenance"
    if in_mm == bool(enter_maintenance_mode):
        ret["comment"] = (
            f"datastore {name!r} already in maintenance mode."
            if in_mm
            else f"datastore {name!r} already out of maintenance mode."
        )
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"datastore {name!r} maintenance mode would change."
        ret["changes"] = {"maintenance": (in_mm, bool(enter_maintenance_mode))}
        return ret
    if enter_maintenance_mode:
        c.enter_maintenance(__opts__, name, profile=profile)
    else:
        c.exit_maintenance(__opts__, name, profile=profile)
    ret["changes"] = {"maintenance": (in_mm, bool(enter_maintenance_mode))}
    ret["comment"] = f"datastore {name!r} maintenance mode updated."
    return ret
