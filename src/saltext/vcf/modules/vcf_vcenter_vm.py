"""Execution module for vCenter VMs."""

from saltext.vcf.clients import vcenter_vm as r

__virtualname__ = "vcf_vcenter_vm"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List VMs known to vCenter.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_vm.list_

    """
    return r.list_(__opts__, profile=profile)


def get(vm, profile=None):
    """Return details for a single VM by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_vm.get <vm>

    """
    return r.get(__opts__, vm, profile=profile)


def power_on(vm, profile=None):
    """Power on a VM.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_vm.power_on <vm>

    """
    return r.power_on(__opts__, vm, profile=profile)


def deploy(name, spec, profile=None):
    """Deploy a VM from a template/source spec or create a bare VM."""
    return r.deploy(__opts__, name, spec, profile=profile)


def wait_reachable(target_ip, port=22, timeout=120, interval=10):
    """Wait for TCP reachability to a VM IP."""
    return r.wait_reachable(target_ip, port=port, timeout=timeout, interval=interval)


def power_off(vm, profile=None):
    """Power off a VM (hard stop).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_vm.power_off <vm>

    """
    return r.power_off(__opts__, vm, profile=profile)


def reset(vm, profile=None):
    """Reset a VM (hard reset).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_vm.reset <vm>

    """
    return r.reset(__opts__, vm, profile=profile)


def search(
    power_states=None,
    names=None,
    hosts=None,
    clusters=None,
    folders=None,
    datacenters=None,
    resource_pools=None,
    vms=None,
    profile=None,
):
    """Server-side VM filtering.

    Pass any combination of ``power_states``, ``names``, ``hosts``, ``clusters``,
    ``folders``, ``datacenters``, ``resource_pools``, ``vms`` as lists. Returns
    the same shape as :func:`list_`.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_vm.search power_states='[POWERED_ON]'

    """
    return r.search(
        __opts__,
        power_states=power_states,
        names=names,
        hosts=hosts,
        clusters=clusters,
        folders=folders,
        datacenters=datacenters,
        resource_pools=resource_pools,
        vms=vms,
        profile=profile,
    )


def tree(profile=None):
    """Return a nested ``{datacenter: {clusters: {cluster: {hosts: {host: {vms: [...]}}}}}}`` map.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_vm.tree

    """
    return r.tree(__opts__, profile=profile)


def summary(profile=None):
    """Aggregate counts: total, by_power_state, by_cpu_count, total_memory_MiB.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_vm.summary

    """
    return r.summary(__opts__, profile=profile)
