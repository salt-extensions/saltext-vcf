"""Execution module for cluster DRS/HA/EVC/DPM settings (SOAP)."""

from saltext.vmware.clients import vim_cluster_config as c

__virtualname__ = "vmware_vim_cluster_config"


def __virtual__():
    return __virtualname__


def drs_get(cluster, profile=None):
    """Return current DRS config.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_cluster_config.drs_get domain-c9
    """
    return c.drs_get(__opts__, cluster, profile=profile)


def drs_set(
    cluster,
    enabled=None,
    default_vm_behavior=None,
    migration_threshold=None,
    vm_monitoring_enabled=None,
    profile=None,
):
    """Update DRS settings.

    *default_vm_behavior*: ``manual`` | ``partiallyAutomated`` | ``fullyAutomated``.
    *migration_threshold*: 1 (conservative) to 5 (aggressive).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_cluster_config.drs_set domain-c9 enabled=true default_vm_behavior=fullyAutomated
    """
    return c.drs_set(
        __opts__,
        cluster,
        enabled=enabled,
        default_vm_behavior=default_vm_behavior,
        migration_threshold=migration_threshold,
        vm_monitoring_enabled=vm_monitoring_enabled,
        profile=profile,
    )


def ha_get(cluster, profile=None):
    """Return current HA config.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_cluster_config.ha_get domain-c9
    """
    return c.ha_get(__opts__, cluster, profile=profile)


def ha_set(
    cluster,
    enabled=None,
    host_monitoring=None,
    vm_monitoring=None,
    restart_priority=None,
    isolation_response=None,
    admission_control_enabled=None,
    profile=None,
):
    """Update HA settings.

    *host_monitoring*: ``enabled`` | ``disabled``.
    *vm_monitoring*: ``vmMonitoringDisabled`` | ``vmMonitoringOnly`` | ``vmAndAppMonitoring``.
    *restart_priority*: ``disabled`` | ``low`` | ``medium`` | ``high`` | ``clusterRestartPriority``.
    *isolation_response*: ``none`` | ``powerOff`` | ``shutdown``.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_cluster_config.ha_set domain-c9 enabled=true vm_monitoring=vmMonitoringOnly
    """
    return c.ha_set(
        __opts__,
        cluster,
        enabled=enabled,
        host_monitoring=host_monitoring,
        vm_monitoring=vm_monitoring,
        restart_priority=restart_priority,
        isolation_response=isolation_response,
        admission_control_enabled=admission_control_enabled,
        profile=profile,
    )


def evc_get(cluster, profile=None):
    """Return the cluster's current EVC mode.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_cluster_config.evc_get domain-c9
    """
    return c.evc_get(__opts__, cluster, profile=profile)


def evc_set(cluster, mode, profile=None):
    """Set the EVC mode (e.g. ``intel-skylake``, ``amd-zen``).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_cluster_config.evc_set domain-c9 intel-skylake
    """
    return c.evc_set(__opts__, cluster, mode, profile=profile)


def evc_disable(cluster, profile=None):
    """Disable EVC on the cluster.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_cluster_config.evc_disable domain-c9
    """
    return c.evc_disable(__opts__, cluster, profile=profile)


def dpm_get(cluster, profile=None):
    """Return the cluster's DPM config.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_cluster_config.dpm_get domain-c9
    """
    return c.dpm_get(__opts__, cluster, profile=profile)


def dpm_set(
    cluster, enabled=None, default_behavior=None, host_power_action_rate=None, profile=None
):
    """Update DPM settings.

    *default_behavior*: ``manual`` | ``automated``.
    *host_power_action_rate*: 1 (conservative) to 5 (aggressive).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_cluster_config.dpm_set domain-c9 enabled=true default_behavior=automated
    """
    return c.dpm_set(
        __opts__,
        cluster,
        enabled=enabled,
        default_behavior=default_behavior,
        host_power_action_rate=host_power_action_rate,
        profile=profile,
    )
