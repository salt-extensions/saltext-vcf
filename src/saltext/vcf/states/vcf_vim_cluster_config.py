"""State module for cluster DRS/HA/EVC/DPM settings."""

from saltext.vcf.clients import vim_cluster_config as c

__virtualname__ = "vcf_vim_cluster_config"


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
    advanced_settings=None,
    profile=None,
):
    """Ensure DRS settings on *cluster* match the provided values.

    Only non-None fields participate in drift detection. *name* is
    informational; *cluster* defaults to *name* when omitted.
    *advanced_settings* is a ``{key: value}`` dict applied to
    ``drsConfig.option``.
    """
    cluster = cluster or name
    ret = _ret(name)
    current = c.drs_get(__opts__, cluster, profile=profile)
    desired = {
        "enabled": enabled,
        "default_vm_behavior": default_vm_behavior,
        "migration_threshold": migration_threshold,
        "vm_monitoring_enabled": vm_monitoring_enabled,
        "advanced_settings": advanced_settings,
    }
    drift = {}
    for k, v in desired.items():
        if v is None:
            continue
        if k == "advanced_settings":
            have = current.get(k) or {}
            drifted = {kk: (have.get(kk), vv) for kk, vv in v.items() if have.get(kk) != vv}
            if drifted:
                drift[k] = drifted
        elif current.get(k) != v:
            drift[k] = (current.get(k), v)
    if not drift:
        ret["comment"] = f"DRS on {cluster} already matches"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"DRS on {cluster} would be updated: {sorted(drift)}"
        return ret
    kwargs = {
        k: v
        for k, v in desired.items()
        if v is not None and (k != "advanced_settings" or drift.get("advanced_settings"))
    }
    c.drs_set(__opts__, cluster, profile=profile, **kwargs)
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
    vm_component_protecting=None,
    vm_min_up_time=None,
    vm_max_failure_window=None,
    vm_max_failures=None,
    vm_failure_interval=None,
    restart_priority_timeout=None,
    enable_apd_timeout_for_hosts=None,
    vm_reaction_on_apd_cleared=None,
    vm_storage_protection_for_apd=None,
    vm_storage_protection_for_pdl=None,
    vm_terminate_delay_for_apd_sec=None,
    admission_control_policy=None,
    advanced_options=None,
    profile=None,
):
    """Ensure HA settings on *cluster* match the provided values (full knob set)."""
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
        "vm_component_protecting": vm_component_protecting,
        "vm_min_up_time": vm_min_up_time,
        "vm_max_failure_window": vm_max_failure_window,
        "vm_max_failures": vm_max_failures,
        "vm_failure_interval": vm_failure_interval,
        "restart_priority_timeout": restart_priority_timeout,
        "enable_apd_timeout_for_hosts": enable_apd_timeout_for_hosts,
        "vm_reaction_on_apd_cleared": vm_reaction_on_apd_cleared,
        "vm_storage_protection_for_apd": vm_storage_protection_for_apd,
        "vm_storage_protection_for_pdl": vm_storage_protection_for_pdl,
        "vm_terminate_delay_for_apd_sec": vm_terminate_delay_for_apd_sec,
        "advanced_settings": advanced_options,
    }
    drift = {}
    for k, v in desired.items():
        if v is None:
            continue
        if k == "advanced_settings":
            have = current.get("advanced_settings") or {}
            drifted = {kk: (have.get(kk), vv) for kk, vv in v.items() if have.get(kk) != vv}
            if drifted:
                drift[k] = drifted
        elif current.get(k) != v:
            drift[k] = (current.get(k), v)
    if not drift:
        ret["comment"] = f"HA on {cluster} already matches"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"HA on {cluster} would be updated: {sorted(drift)}"
        return ret
    kwargs = {
        k: v
        for k, v in desired.items()
        if v is not None and (k != "advanced_settings" or drift.get("advanced_settings"))
    }
    if admission_control_policy is not None:
        kwargs["admission_control_policy"] = admission_control_policy
    c.ha_set(__opts__, cluster, profile=profile, **kwargs)
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
