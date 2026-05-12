"""Per-VM / per-host cluster-level overrides via SOAP.

These are the rows in vSphere's "Cluster -> Configure -> VM/Host Rules /
Overrides" view that let you make a single VM (or host) behave differently
from the cluster default:

- **DRS VM override** — change a VM's automation level (manual /
  partiallyAutomated / fullyAutomated / disabled) regardless of the cluster
  default.
- **HA VM override** — change a VM's restart priority, isolation response,
  PDL/APD failover behaviour.
- **DPM host override** — change a single host's DPM behaviour (the cluster
  default puts everyone in automatic; an override pins one host to manual or
  disabled).

All writes go through ``ClusterComputeResource.ReconfigureComputeResource_Task``
with a ``vim.cluster.ConfigSpecEx`` that carries the relevant config-spec list.
"""

from pyVmomi import vim

from saltext.vmware.clients.vim_cluster_config import _cluster


def _drs_behavior(value):
    return vim.cluster.DrsConfigInfo.DrsBehavior(value)


def _restart_priority(value):
    return vim.cluster.DasVmSettings.RestartPriority(value)


def _isolation_response(value):
    return vim.cluster.DasVmSettings.IsolationResponse(value)


def _dpm_behavior(value):
    return vim.cluster.DpmConfigInfo.DpmBehavior(value)


def _resolve_vm(opts, vm_moid):
    """Build a managed-object reference to a VM. Doesn't require a round-trip."""
    return vim.VirtualMachine(vm_moid, None)


def _resolve_host(opts, host_moid):
    return vim.HostSystem(host_moid, None)


# ---------------------------------------------------------------------------
# DRS VM overrides
# ---------------------------------------------------------------------------


def drs_vm_list(opts, cluster, profile=None):
    """List per-VM DRS overrides on *cluster*."""
    cl = _cluster(opts, cluster, profile=profile)
    out = []
    for entry in cl.configurationEx.drsVmConfig or []:
        out.append(
            {
                "vm_moid": entry.key._moId,  # noqa: SLF001
                "enabled": bool(getattr(entry, "enabled", True)),
                "behavior": str(entry.behavior) if entry.behavior else None,
            }
        )
    return out


def drs_vm_set(opts, cluster, vm_moid, behavior, enabled=True, profile=None):
    """Add or replace the DRS override for *vm_moid* on *cluster*.

    *behavior*: ``manual`` | ``partiallyAutomated`` | ``fullyAutomated`` |
    ``disabled``.
    """
    cl = _cluster(opts, cluster, profile=profile)
    existing = [e.key._moId for e in cl.configurationEx.drsVmConfig or []]  # noqa: SLF001
    op = "edit" if vm_moid in existing else "add"
    info = vim.cluster.DrsVmConfigInfo(
        key=_resolve_vm(opts, vm_moid),
        enabled=bool(enabled),
        behavior=_drs_behavior(behavior),
    )
    spec = vim.cluster.ConfigSpecEx(
        drsVmConfigSpec=[vim.cluster.DrsVmConfigSpec(operation=op, info=info)]
    )
    task = cl.ReconfigureComputeResource_Task(spec=spec, modify=True)
    return task._moId  # noqa: SLF001


def drs_vm_remove(opts, cluster, vm_moid, profile=None):
    """Remove the DRS override for *vm_moid* — the VM goes back to the cluster default."""
    cl = _cluster(opts, cluster, profile=profile)
    spec = vim.cluster.ConfigSpecEx(
        drsVmConfigSpec=[
            vim.cluster.DrsVmConfigSpec(operation="remove", removeKey=_resolve_vm(opts, vm_moid))
        ]
    )
    task = cl.ReconfigureComputeResource_Task(spec=spec, modify=True)
    return task._moId  # noqa: SLF001


# ---------------------------------------------------------------------------
# HA VM overrides
# ---------------------------------------------------------------------------


def ha_vm_list(opts, cluster, profile=None):
    cl = _cluster(opts, cluster, profile=profile)
    out = []
    for entry in cl.configurationEx.dasVmConfig or []:
        ds = entry.dasSettings or vim.cluster.DasVmSettings()
        out.append(
            {
                "vm_moid": entry.key._moId,  # noqa: SLF001
                "restart_priority": str(ds.restartPriority) if ds.restartPriority else None,
                "isolation_response": str(ds.isolationResponse) if ds.isolationResponse else None,
            }
        )
    return out


def ha_vm_set(
    opts,
    cluster,
    vm_moid,
    restart_priority=None,
    isolation_response=None,
    profile=None,
):
    """Add or replace the HA override for *vm_moid* on *cluster*.

    *restart_priority*: ``disabled`` | ``lowest`` | ``low`` | ``medium`` |
    ``high`` | ``highest`` | ``clusterRestartPriority``.
    *isolation_response*: ``none`` | ``powerOff`` | ``shutdown`` |
    ``clusterIsolationResponse``.
    """
    cl = _cluster(opts, cluster, profile=profile)
    existing = [e.key._moId for e in cl.configurationEx.dasVmConfig or []]  # noqa: SLF001
    op = "edit" if vm_moid in existing else "add"
    settings = vim.cluster.DasVmSettings()
    if restart_priority is not None:
        settings.restartPriority = _restart_priority(restart_priority)
    if isolation_response is not None:
        settings.isolationResponse = _isolation_response(isolation_response)
    info = vim.cluster.DasVmConfigInfo(
        key=_resolve_vm(opts, vm_moid),
        dasSettings=settings,
    )
    spec = vim.cluster.ConfigSpecEx(
        dasVmConfigSpec=[vim.cluster.DasVmConfigSpec(operation=op, info=info)]
    )
    task = cl.ReconfigureComputeResource_Task(spec=spec, modify=True)
    return task._moId  # noqa: SLF001


def ha_vm_remove(opts, cluster, vm_moid, profile=None):
    cl = _cluster(opts, cluster, profile=profile)
    spec = vim.cluster.ConfigSpecEx(
        dasVmConfigSpec=[
            vim.cluster.DasVmConfigSpec(operation="remove", removeKey=_resolve_vm(opts, vm_moid))
        ]
    )
    task = cl.ReconfigureComputeResource_Task(spec=spec, modify=True)
    return task._moId  # noqa: SLF001


# ---------------------------------------------------------------------------
# DPM host overrides
# ---------------------------------------------------------------------------


def dpm_host_list(opts, cluster, profile=None):
    cl = _cluster(opts, cluster, profile=profile)
    out = []
    for entry in cl.configurationEx.dpmHostConfig or []:
        out.append(
            {
                "host_moid": entry.key._moId,  # noqa: SLF001
                "enabled": bool(getattr(entry, "enabled", True)),
                "behavior": str(entry.behavior) if entry.behavior else None,
            }
        )
    return out


def dpm_host_set(opts, cluster, host_moid, behavior, enabled=True, profile=None):
    """*behavior*: ``manual`` | ``automated``."""
    cl = _cluster(opts, cluster, profile=profile)
    existing = [e.key._moId for e in cl.configurationEx.dpmHostConfig or []]  # noqa: SLF001
    op = "edit" if host_moid in existing else "add"
    info = vim.cluster.DpmHostConfigInfo(
        key=_resolve_host(opts, host_moid),
        enabled=bool(enabled),
        behavior=_dpm_behavior(behavior),
    )
    spec = vim.cluster.ConfigSpecEx(
        dpmHostConfigSpec=[vim.cluster.DpmHostConfigSpec(operation=op, info=info)]
    )
    task = cl.ReconfigureComputeResource_Task(spec=spec, modify=True)
    return task._moId  # noqa: SLF001


def dpm_host_remove(opts, cluster, host_moid, profile=None):
    cl = _cluster(opts, cluster, profile=profile)
    spec = vim.cluster.ConfigSpecEx(
        dpmHostConfigSpec=[
            vim.cluster.DpmHostConfigSpec(
                operation="remove", removeKey=_resolve_host(opts, host_moid)
            )
        ]
    )
    task = cl.ReconfigureComputeResource_Task(spec=spec, modify=True)
    return task._moId  # noqa: SLF001
