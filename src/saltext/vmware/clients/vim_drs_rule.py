"""Cluster DRS affinity / anti-affinity rules via SOAP.

Three rule kinds:

* **VM-VM affinity** (``vim.cluster.AffinityRuleSpec``) — keep VMs together
* **VM-VM anti-affinity** (``vim.cluster.AntiAffinityRuleSpec``) — keep VMs apart
* **VM-Host** (``vim.cluster.VmHostRuleInfo``) — bind/exclude a VM group to/from
  a host group

Rules are mutated through ``ClusterComputeResource.ReconfigureComputeResource_Task``
with a ``vim.cluster.ConfigSpecEx`` containing ``rulesSpec`` operations.

Rule identity:

- pyVmomi servers assign a stable ``key`` (int) to each rule.
- A separate ``name`` is the human-readable label. Names are unique within a
  cluster on practical deployments; we use it as the lookup key.
"""

from pyVmomi import vim

from saltext.vmware.utils import vim as soap


def _cluster(opts, cluster_name, profile=None):
    content = soap.content(opts, profile=profile)
    for dc in content.rootFolder.childEntity:
        if not isinstance(dc, vim.Datacenter):
            continue
        for entity in dc.hostFolder.childEntity:
            if isinstance(entity, vim.ClusterComputeResource) and cluster_name in (
                entity._moId,  # noqa: SLF001
                entity.name,
            ):
                return entity
    raise LookupError(f"cluster {cluster_name!r} not found")


def list_(opts, cluster, profile=None):
    """Return every DRS rule on *cluster* as a list of dicts."""
    cl = _cluster(opts, cluster, profile=profile)
    out = []
    for rule in cl.configurationEx.rule or []:
        out.append(_to_dict(rule))
    return out


def get(opts, cluster, name, profile=None):
    cl = _cluster(opts, cluster, profile=profile)
    for rule in cl.configurationEx.rule or []:
        if rule.name == name:
            return _to_dict(rule)
    raise LookupError(f"DRS rule {name!r} not found on cluster {cluster!r}")


def get_or_none(opts, cluster, name, profile=None):
    try:
        return get(opts, cluster, name, profile=profile)
    except LookupError:
        return None


def create_vm_affinity(opts, cluster, name, vm_moids, enabled=True, mandatory=False, profile=None):
    """Create a VM-VM affinity rule keeping *vm_moids* on the same host."""
    return _apply(
        opts,
        cluster,
        vim.cluster.AffinityRuleSpec(
            name=name,
            enabled=enabled,
            mandatory=mandatory,
            vm=[_vm_ref(opts, m, profile=profile) for m in vm_moids],
        ),
        operation="add",
        profile=profile,
    )


def create_vm_anti_affinity(
    opts, cluster, name, vm_moids, enabled=True, mandatory=False, profile=None
):
    """Create a VM-VM anti-affinity rule keeping *vm_moids* on different hosts."""
    return _apply(
        opts,
        cluster,
        vim.cluster.AntiAffinityRuleSpec(
            name=name,
            enabled=enabled,
            mandatory=mandatory,
            vm=[_vm_ref(opts, m, profile=profile) for m in vm_moids],
        ),
        operation="add",
        profile=profile,
    )


def create_vm_host(
    opts,
    cluster,
    name,
    vm_group_name,
    host_group_name,
    affine=True,
    mandatory=False,
    enabled=True,
    profile=None,
):
    """Create a VM-Host rule binding *vm_group_name* to *host_group_name*.

    *affine* True means *runVmOnHost*; False is *runVmAvoidHost*.
    """
    rule = vim.cluster.VmHostRuleInfo(
        name=name,
        enabled=enabled,
        mandatory=mandatory,
        vmGroupName=vm_group_name,
    )
    if affine:
        rule.affineHostGroupName = host_group_name
    else:
        rule.antiAffineHostGroupName = host_group_name
    return _apply(opts, cluster, rule, operation="add", profile=profile)


def update(opts, cluster, name, enabled=None, mandatory=None, vm_moids=None, profile=None):
    """Modify an existing rule's enabled/mandatory flags and/or its VM set.

    Only fields that are not ``None`` are touched. Returns the updated rule dict.
    """
    cl = _cluster(opts, cluster, profile=profile)
    rule = _find_rule(cl, name)
    if enabled is not None:
        rule.enabled = enabled
    if mandatory is not None:
        rule.mandatory = mandatory
    if vm_moids is not None and hasattr(rule, "vm"):
        rule.vm = [_vm_ref(opts, m, profile=profile) for m in vm_moids]
    return _apply(opts, cluster, rule, operation="edit", profile=profile)


def delete(opts, cluster, name, profile=None):
    cl = _cluster(opts, cluster, profile=profile)
    rule = _find_rule(cl, name)
    spec = vim.cluster.ConfigSpecEx(
        rulesSpec=[vim.cluster.RuleSpec(operation="remove", removeKey=rule.key)]
    )
    task = cl.ReconfigureComputeResource_Task(spec=spec, modify=True)
    return task._moId  # noqa: SLF001


# ---------------------------------------------------------------------------
# VM / Host groups (prereq for VM-Host rules)
# ---------------------------------------------------------------------------


def list_groups(opts, cluster, profile=None):
    cl = _cluster(opts, cluster, profile=profile)
    out = []
    for grp in cl.configurationEx.group or []:
        kind = "vm" if isinstance(grp, vim.cluster.VmGroup) else "host"
        members = [m._moId for m in (grp.vm if kind == "vm" else grp.host) or []]  # noqa: SLF001
        out.append({"name": grp.name, "kind": kind, "members": members})
    return out


def create_vm_group(opts, cluster, name, vm_moids, profile=None):
    grp = vim.cluster.VmGroup(name=name, vm=[_vm_ref(opts, m, profile=profile) for m in vm_moids])
    spec = vim.cluster.ConfigSpecEx(groupSpec=[vim.cluster.GroupSpec(operation="add", info=grp)])
    cl = _cluster(opts, cluster, profile=profile)
    task = cl.ReconfigureComputeResource_Task(spec=spec, modify=True)
    return task._moId  # noqa: SLF001


def create_host_group(opts, cluster, name, host_moids, profile=None):
    grp = vim.cluster.HostGroup(
        name=name, host=[_host_ref(opts, m, profile=profile) for m in host_moids]
    )
    spec = vim.cluster.ConfigSpecEx(groupSpec=[vim.cluster.GroupSpec(operation="add", info=grp)])
    cl = _cluster(opts, cluster, profile=profile)
    task = cl.ReconfigureComputeResource_Task(spec=spec, modify=True)
    return task._moId  # noqa: SLF001


def delete_group(opts, cluster, name, profile=None):
    spec = vim.cluster.ConfigSpecEx(
        groupSpec=[vim.cluster.GroupSpec(operation="remove", removeKey=name)]
    )
    cl = _cluster(opts, cluster, profile=profile)
    task = cl.ReconfigureComputeResource_Task(spec=spec, modify=True)
    return task._moId  # noqa: SLF001


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _apply(opts, cluster, rule, operation, profile=None):
    cl = _cluster(opts, cluster, profile=profile)
    rule_spec = vim.cluster.RuleSpec(operation=operation, info=rule)
    if operation == "edit":
        rule_spec.removeKey = rule.key
    spec = vim.cluster.ConfigSpecEx(rulesSpec=[rule_spec])
    task = cl.ReconfigureComputeResource_Task(spec=spec, modify=True)
    return task._moId  # noqa: SLF001


def _find_rule(cluster_obj, name):
    for rule in cluster_obj.configurationEx.rule or []:
        if rule.name == name:
            return rule
    raise LookupError(f"DRS rule {name!r} not found")


def _vm_ref(opts, moid, profile=None):
    content = soap.content(opts, profile=profile)
    obj = vim.VirtualMachine(moid, content.searchIndex._stub)  # noqa: SLF001
    return obj


def _host_ref(opts, moid, profile=None):
    content = soap.content(opts, profile=profile)
    obj = vim.HostSystem(moid, content.searchIndex._stub)  # noqa: SLF001
    return obj


def _to_dict(rule):
    out = {
        "key": rule.key,
        "name": rule.name,
        "enabled": bool(rule.enabled),
        "mandatory": bool(rule.mandatory),
        "user_created": bool(getattr(rule, "userCreated", True)),
        "in_compliance": bool(getattr(rule, "inCompliance", True)),
    }
    if isinstance(rule, (vim.cluster.AntiAffinityRuleSpec, vim.cluster.AffinityRuleSpec)):
        out["kind"] = (
            "vm-anti-affinity"
            if isinstance(rule, vim.cluster.AntiAffinityRuleSpec)
            else "vm-affinity"
        )
        out["vm_moids"] = [v._moId for v in (rule.vm or [])]  # noqa: SLF001
    elif isinstance(rule, vim.cluster.VmHostRuleInfo):
        out["kind"] = "vm-host"
        out["vm_group_name"] = rule.vmGroupName
        out["affine_host_group_name"] = getattr(rule, "affineHostGroupName", None)
        out["anti_affine_host_group_name"] = getattr(rule, "antiAffineHostGroupName", None)
    else:
        out["kind"] = type(rule).__name__
    return out
