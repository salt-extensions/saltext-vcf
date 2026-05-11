"""State module for cluster DRS/HA/EVC/DPM settings."""

from saltext.vmware.clients import vim_cluster_config as c

__virtualname__ = "vmware_vim_cluster_config"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def drs(
    name,
    cluster=None,
    enabled=None,
    default_vm_behavior=None,
    migration_threshold=None,
    vm_monitoring_enabled=None,
    profile=None,
):
    """Ensure DRS settings on *cluster* match the provided values.

    Only non-None fields participate in drift detection. *name* is
    informational; *cluster* defaults to *name* when omitted.
    """
    cluster = cluster or name
    ret = _ret(name)
    current = c.drs_get(__opts__, cluster, profile=profile)
    desired = {
        "enabled": enabled,
        "default_vm_behavior": default_vm_behavior,
        "migration_threshold": migration_threshold,
        "vm_monitoring_enabled": vm_monitoring_enabled,
    }
    drift = {
        k: (current.get(k), v) for k, v in desired.items() if v is not None and current.get(k) != v
    }
    if not drift:
        ret["comment"] = f"DRS on {cluster} already matches"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"DRS on {cluster} would be updated: {sorted(drift)}"
        return ret
    c.drs_set(
        __opts__, cluster, profile=profile, **{k: v for k, v in desired.items() if v is not None}
    )
    ret["changes"] = drift
    ret["comment"] = f"DRS on {cluster} updated"
    return ret


def ha(
    name,
    cluster=None,
    enabled=None,
    host_monitoring=None,
    vm_monitoring=None,
    restart_priority=None,
    isolation_response=None,
    admission_control_enabled=None,
    profile=None,
):
    """Ensure HA settings on *cluster* match the provided values."""
    cluster = cluster or name
    ret = _ret(name)
    current = c.ha_get(__opts__, cluster, profile=profile)
    desired = {
        "enabled": enabled,
        "host_monitoring": host_monitoring,
        "vm_monitoring": vm_monitoring,
        "restart_priority": restart_priority,
        "isolation_response": isolation_response,
        "admission_control_enabled": admission_control_enabled,
    }
    drift = {
        k: (current.get(k), v) for k, v in desired.items() if v is not None and current.get(k) != v
    }
    if not drift:
        ret["comment"] = f"HA on {cluster} already matches"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"HA on {cluster} would be updated: {sorted(drift)}"
        return ret
    c.ha_set(
        __opts__, cluster, profile=profile, **{k: v for k, v in desired.items() if v is not None}
    )
    ret["changes"] = drift
    ret["comment"] = f"HA on {cluster} updated"
    return ret


def evc(name, cluster=None, mode=None, profile=None):
    """Ensure EVC on *cluster* matches *mode* (or is disabled when ``None``)."""
    cluster = cluster or name
    ret = _ret(name)
    current = c.evc_get(__opts__, cluster, profile=profile)
    current_mode = current.get("current_mode")
    if current_mode == mode:
        ret["comment"] = f"EVC on {cluster} already at {mode!r}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"EVC on {cluster} would change from {current_mode!r} to {mode!r}"
        return ret
    if mode is None:
        c.evc_disable(__opts__, cluster, profile=profile)
    else:
        c.evc_set(__opts__, cluster, mode, profile=profile)
    ret["changes"] = {"mode": (current_mode, mode)}
    ret["comment"] = f"EVC on {cluster} set to {mode!r}"
    return ret
