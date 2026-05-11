"""State module for cluster DRS rules."""

from saltext.vmware.clients import vim_drs_rule as c

__virtualname__ = "vmware_vim_drs_rule"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def vm_affinity(name, cluster, vm_moids, enabled=True, mandatory=False, profile=None):
    """Ensure a VM-VM affinity rule exists keeping *vm_moids* together."""
    return _present_vm_rule(name, cluster, vm_moids, "vm-affinity", enabled, mandatory, profile)


def vm_anti_affinity(name, cluster, vm_moids, enabled=True, mandatory=False, profile=None):
    """Ensure a VM-VM anti-affinity rule exists keeping *vm_moids* apart."""
    return _present_vm_rule(
        name, cluster, vm_moids, "vm-anti-affinity", enabled, mandatory, profile
    )


def absent(name, cluster, profile=None):
    """Ensure a DRS rule with this name does not exist on *cluster*."""
    ret = _ret(name)
    existing = c.get_or_none(__opts__, cluster, name, profile=profile)
    if existing is None:
        ret["comment"] = f"DRS rule {name} is already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"DRS rule {name} would be deleted"
        return ret
    c.delete(__opts__, cluster, name, profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"DRS rule {name} deleted"
    return ret


def _present_vm_rule(name, cluster, vm_moids, kind, enabled, mandatory, profile):
    ret = _ret(name)
    existing = c.get_or_none(__opts__, cluster, name, profile=profile)
    desired = sorted(set(vm_moids))
    if existing is not None:
        if existing.get("kind") != kind:
            ret["result"] = False
            ret["comment"] = (
                f"DRS rule {name} exists but has kind {existing['kind']!r} "
                f"(wanted {kind!r}); refusing to mutate kind"
            )
            return ret
        current = sorted(set(existing.get("vm_moids", [])))
        drift = {}
        if current != desired:
            drift["vm_moids"] = (current, desired)
        if bool(existing.get("enabled")) != bool(enabled):
            drift["enabled"] = (existing.get("enabled"), enabled)
        if bool(existing.get("mandatory")) != bool(mandatory):
            drift["mandatory"] = (existing.get("mandatory"), mandatory)
        if not drift:
            ret["comment"] = f"DRS rule {name} already matches"
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"DRS rule {name} would be updated: {sorted(drift)}"
            return ret
        c.update(
            __opts__,
            cluster,
            name,
            enabled=enabled,
            mandatory=mandatory,
            vm_moids=desired,
            profile=profile,
        )
        ret["changes"] = drift
        ret["comment"] = f"DRS rule {name} updated"
        return ret

    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"DRS rule {name} would be created"
        return ret
    if kind == "vm-affinity":
        c.create_vm_affinity(
            __opts__, cluster, name, desired, enabled=enabled, mandatory=mandatory, profile=profile
        )
    else:
        c.create_vm_anti_affinity(
            __opts__, cluster, name, desired, enabled=enabled, mandatory=mandatory, profile=profile
        )
    ret["changes"] = {"new": name, "kind": kind, "vm_moids": desired}
    ret["comment"] = f"DRS rule {name} created"
    return ret
