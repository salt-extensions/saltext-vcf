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
    """Deploy a VM from a template/source spec or create a bare VM.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_vm.deploy web-01 spec='{"source": "vm-42", "folder": "group-v3", "datastore": "datastore-13"}'
    """
    return r.deploy(__opts__, name, spec, profile=profile)


def wait_reachable(target_ip, port=22, timeout=120, interval=10):
    """Wait for TCP reachability to a VM IP.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_vm.wait_reachable 10.0.0.5 port=22
    """
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


def _resolve_deploy_creds(host, username, password, profile):
    """Resolve OVF/OVA deploy connection parameters from pillar when not passed."""
    import saltext.vcf.utils.esxi as esxi_conn  # noqa: PLC0415
    import saltext.vcf.utils.vim as soap  # noqa: PLC0415

    if host is None:
        if soap.is_standalone_esxi(__opts__, profile=profile):
            cfg = esxi_conn.get_config(__opts__, profile=profile)
        else:
            cfg = esxi_conn.get_config(__opts__, profile=profile) or {}
            if not cfg.get("host"):
                import saltext.vcf.utils.vcenter as vc_rest  # noqa: PLC0415

                cfg = vc_rest.get_config(__opts__, profile=profile)
        host = cfg.get("host")
        username = username or cfg.get("username")
        password = password or cfg.get("password")
    if not host:
        raise ValueError(
            "target host unknown: pass host=/username=/password= or configure "
            "saltext.vcf.esxi / saltext.vcf.vcenter in pillar"
        )
    return host, username, password


def deploy_ova(
    vm_name,
    ova_source,
    host=None,
    username=None,
    password=None,
    datastore=None,
    network_map=None,
    ovf_properties=None,
    disk_provisioning="thin",
    deployment_option=None,
    power_on=True,
    verify_ssl=None,
    backend="pyvmomi",
    profile=None,
):
    """Deploy an OVA to *host* (ESXi standalone or vCenter).

    Connection parameters default to the configured pillar profile
    (``saltext.vcf.esxi`` or ``saltext.vcf.vcenter``). *backend* selects
    ``pyvmomi`` (in-process NFC upload) or ``ovftool`` (subprocess).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_vm.deploy_ova appliance-01 /opt/ova/app.ova host=10.0.0.5 datastore=ds1
    """
    import saltext.vcf.utils.vim as soap  # noqa: PLC0415

    host, username, password = _resolve_deploy_creds(host, username, password, profile)
    if verify_ssl is None:
        if soap.is_standalone_esxi(__opts__, profile=profile):
            import saltext.vcf.utils.esxi as esxi_conn  # noqa: PLC0415

            verify_ssl = bool(esxi_conn.get_config(__opts__, profile=profile).get("verify_ssl"))
        else:
            import saltext.vcf.utils.vcenter as vc_rest  # noqa: PLC0415

            verify_ssl = bool(vc_rest.get_config(__opts__, profile=profile).get("verify_ssl"))
    if backend == "ovftool":
        from saltext.vcf.clients import ovftool_deploy  # noqa: PLC0415

        return ovftool_deploy.deploy_ova(
            ova_source=ova_source,
            target_host=host,
            target_user=username,
            target_password=password,
            vm_name=vm_name,
            datastore=datastore,
            network_map=network_map,
            ovf_properties=ovf_properties,
            disk_provisioning=disk_provisioning,
            deployment_option=deployment_option,
            power_on=power_on,
            verify_ssl=verify_ssl,
        )
    from saltext.vcf.clients import ovf_deploy  # noqa: PLC0415

    return ovf_deploy.deploy_ova(
        ova_source=ova_source,
        target_host=host,
        target_user=username,
        target_password=password,
        vm_name=vm_name,
        datastore=datastore,
        network_map=network_map,
        ovf_properties=ovf_properties,
        disk_provisioning=disk_provisioning,
        deployment_option=deployment_option,
        power_on=power_on,
        verify_ssl=verify_ssl,
    )


def deploy_ovf(
    vm_name,
    ovf_source,
    host=None,
    username=None,
    password=None,
    datastore=None,
    network_map=None,
    ovf_properties=None,
    disk_provisioning="thin",
    deployment_option=None,
    power_on=True,
    verify_ssl=None,
    profile=None,
):
    """Deploy a raw OVF (``.ovf`` file or directory with ``.mf``/``.vmdk`` sidecars).

    Connection parameters default to the configured pillar profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_vm.deploy_ovf app-01 /opt/ovf/app.ovf host=10.0.0.5 datastore=ds1
    """
    return deploy_ova(
        vm_name,
        ovf_source,
        host=host,
        username=username,
        password=password,
        datastore=datastore,
        network_map=network_map,
        ovf_properties=ovf_properties,
        disk_provisioning=disk_provisioning,
        deployment_option=deployment_option,
        power_on=power_on,
        verify_ssl=verify_ssl,
        backend="pyvmomi",
        profile=profile,
    )
