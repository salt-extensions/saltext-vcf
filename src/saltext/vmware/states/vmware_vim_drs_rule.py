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


def vm_host(
    name,
    cluster,
    vm_group_name,
    host_group_name,
    affine=True,
    enabled=True,
    mandatory=False,
    profile=None,
):
    """Ensure a VM-Host DRS rule binds *vm_group_name* to *host_group_name*.

    *affine* True → runVmOnHost; False → runVmAvoidHost.
    """
    ret = _ret(name)
    existing = c.get_or_none(__opts__, cluster, name, profile=profile)
    if existing is not None:
        if existing.get("kind") != "vm-host":
            ret["result"] = False
            ret["comment"] = (
                f"DRS rule {name} exists but has kind {existing['kind']!r}; refusing to mutate kind"
            )
            return ret
        cur_aff = existing.get("affine_host_group_name")
        cur_anti = existing.get("anti_affine_host_group_name")
        drift = {}
        if existing.get("vm_group_name") != vm_group_name:
            drift["vm_group_name"] = (existing.get("vm_group_name"), vm_group_name)
        if affine:
            if cur_aff != host_group_name or cur_anti is not None:
                drift["host_group_name"] = (cur_anti or cur_aff, host_group_name)
                drift["affine"] = (cur_anti is None, True)
        else:
            if cur_anti != host_group_name or cur_aff is not None:
                drift["host_group_name"] = (cur_aff or cur_anti, host_group_name)
                drift["affine"] = (cur_aff is not None, False)
        if bool(existing.get("enabled")) != bool(enabled):
            drift["enabled"] = (existing.get("enabled"), enabled)
        if bool(existing.get("mandatory")) != bool(mandatory):
            drift["mandatory"] = (existing.get("mandatory"), mandatory)
        if not drift:
            ret["comment"] = f"VM-Host rule {name} already matches"
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"VM-Host rule {name} would change: {sorted(drift)}"
            return ret
        # SOAP edit on VmHostRuleInfo replaces the rule wholesale; recreate is simpler.
        c.delete(__opts__, cluster, name, profile=profile)
        c.create_vm_host(
            __opts__,
            cluster,
            name,
            vm_group_name,
            host_group_name,
            affine=affine,
            enabled=enabled,
            mandatory=mandatory,
            profile=profile,
        )
        ret["changes"] = drift
        ret["comment"] = f"VM-Host rule {name} updated"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"VM-Host rule {name} would be created"
        return ret
    c.create_vm_host(
        __opts__,
        cluster,
        name,
        vm_group_name,
        host_group_name,
        affine=affine,
        enabled=enabled,
        mandatory=mandatory,
        profile=profile,
    )
    ret["changes"] = {
        "new": name,
        "vm_group": vm_group_name,
        "host_group": host_group_name,
        "affine": bool(affine),
    }
    ret["comment"] = f"VM-Host rule {name} created"
    return ret


def vm_group(name, cluster, vm_moids, profile=None):
    """Ensure a DRS VM group with *vm_moids* exists on *cluster*."""
    ret = _ret(name)
    desired = sorted(set(vm_moids))
    existing = c.get_group_or_none(__opts__, cluster, name, profile=profile)
    if existing is not None:
        if existing.get("kind") != "vm":
            ret["result"] = False
            ret["comment"] = f"group {name} exists but is a host group"
            return ret
        current = sorted(set(existing.get("members", [])))
        if current == desired:
            ret["comment"] = f"VM group {name} already matches"
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"VM group {name} membership would change"
            return ret
        c.update_group(__opts__, cluster, name, vm_moids=desired, profile=profile)
        ret["changes"] = {"members": (current, desired)}
        ret["comment"] = f"VM group {name} updated"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"VM group {name} would be created"
        return ret
    c.create_vm_group(__opts__, cluster, name, desired, profile=profile)
    ret["changes"] = {"new": name, "members": desired}
    ret["comment"] = f"VM group {name} created"
    return ret


def host_group(name, cluster, host_moids, profile=None):
    """Ensure a DRS host group with *host_moids* exists on *cluster*."""
    ret = _ret(name)
    desired = sorted(set(host_moids))
    existing = c.get_group_or_none(__opts__, cluster, name, profile=profile)
    if existing is not None:
        if existing.get("kind") != "host":
            ret["result"] = False
            ret["comment"] = f"group {name} exists but is a VM group"
            return ret
        current = sorted(set(existing.get("members", [])))
        if current == desired:
            ret["comment"] = f"host group {name} already matches"
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"host group {name} membership would change"
            return ret
        c.update_group(__opts__, cluster, name, host_moids=desired, profile=profile)
        ret["changes"] = {"members": (current, desired)}
        ret["comment"] = f"host group {name} updated"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"host group {name} would be created"
        return ret
    c.create_host_group(__opts__, cluster, name, desired, profile=profile)
    ret["changes"] = {"new": name, "members": desired}
    ret["comment"] = f"host group {name} created"
    return ret


def group_absent(name, cluster, profile=None):
    """Ensure a DRS VM or host group with this name does not exist."""
    ret = _ret(name)
    existing = c.get_group_or_none(__opts__, cluster, name, profile=profile)
    if existing is None:
        ret["comment"] = f"group {name} already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"group {name} would be deleted"
        return ret
    c.delete_group(__opts__, cluster, name, profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"group {name} deleted"
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
