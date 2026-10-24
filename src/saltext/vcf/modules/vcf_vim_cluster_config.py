"""Execution module for cluster DRS/HA/EVC/DPM settings (SOAP)."""

from saltext.vcf.clients import vim_cluster_config as c

__virtualname__ = "vcf_vim_cluster_config"


def __virtual__():
    return __virtualname__


def drs_get(cluster, profile=None):
    """Return current DRS config.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_cluster_config.drs_get domain-c9
    """
    return c.drs_get(__opts__, cluster, profile=profile)


def drs_set(
    cluster,
    enabled=None,
    default_vm_behavior=None,
    migration_threshold=None,
    vm_monitoring_enabled=None,
    advanced_settings=None,
    vmotion_rate=None,
    profile=None,
):
    """Update DRS settings.

    *default_vm_behavior*: ``manual`` | ``partiallyAutomated`` | ``fullyAutomated``.
    *migration_threshold*: raw ``vmotionRate`` 1 (aggressive) to 5 (conservative).
    *vmotion_rate*: user-friendly scale — 1 (conservative) to 5 (aggressive);
    converted internally (``6 - vmotion_rate``). Supersedes *migration_threshold*
    when both are given.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_cluster_config.drs_set domain-c9 enabled=true default_vm_behavior=fullyAutomated
    """
    if migration_threshold is None and vmotion_rate is not None:
        migration_threshold = 6 - int(vmotion_rate)
    return c.drs_set(
        __opts__,
        cluster,
        enabled=enabled,
        default_vm_behavior=default_vm_behavior,
        migration_threshold=migration_threshold,
        vm_monitoring_enabled=vm_monitoring_enabled,
        advanced_settings=advanced_settings,
        profile=profile,
    )


def get_config(cluster, profile=None):
    """Aggregate DRS + HA + vSAN enablement for *cluster*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_cluster_config.get_config domain-c9
    """
    return c.get_config(__opts__, cluster, profile=profile)


def ha_get(cluster, profile=None):
    """Return current HA config.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_cluster_config.ha_get domain-c9
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
    """Update HA settings (full ``vim.cluster.ConfigSpecEx.dasConfig`` surface).

    *host_monitoring*: ``enabled`` | ``disabled``.
    *vm_monitoring*: ``vmMonitoringDisabled`` | ``vmMonitoringOnly`` | ``vmAndAppMonitoring``.
    *restart_priority*: ``disabled`` | ``low`` | ``medium`` | ``high`` | ``clusterRestartPriority``.
    *isolation_response*: ``none`` | ``powerOff`` | ``shutdown``.
    *admission_control_policy*: dict with one of
      ``slot_based_admission_control``, ``failover_host_admission_control``,
      ``reservation_based_admission_control`` (each with ``failover_level`` and
      policy-specific fields).
    *advanced_options*: ``{key: value}`` applied to ``dasConfig.option``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_cluster_config.ha_set domain-c9 enabled=true vm_monitoring=vmMonitoringOnly
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
        vm_component_protecting=vm_component_protecting,
        vm_min_up_time=vm_min_up_time,
        vm_max_failure_window=vm_max_failure_window,
        vm_max_failures=vm_max_failures,
        vm_failure_interval=vm_failure_interval,
        restart_priority_timeout=restart_priority_timeout,
        enable_apd_timeout_for_hosts=enable_apd_timeout_for_hosts,
        vm_reaction_on_apd_cleared=vm_reaction_on_apd_cleared,
        vm_storage_protection_for_apd=vm_storage_protection_for_apd,
        vm_storage_protection_for_pdl=vm_storage_protection_for_pdl,
        vm_terminate_delay_for_apd_sec=vm_terminate_delay_for_apd_sec,
        admission_control_policy=admission_control_policy,
        advanced_options=advanced_options,
        profile=profile,
    )


def evc_get(cluster, profile=None):
    """Return the cluster's current EVC mode.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_cluster_config.evc_get domain-c9
    """
    return c.evc_get(__opts__, cluster, profile=profile)


def evc_set(cluster, mode, profile=None):
    """Set the EVC mode (e.g. ``intel-skylake``, ``amd-zen``).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_cluster_config.evc_set domain-c9 intel-skylake
    """
    return c.evc_set(__opts__, cluster, mode, profile=profile)


def evc_disable(cluster, profile=None):
    """Disable EVC on the cluster.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_cluster_config.evc_disable domain-c9
    """
    return c.evc_disable(__opts__, cluster, profile=profile)


def dpm_get(cluster, profile=None):
    """Return the cluster's DPM config.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_cluster_config.dpm_get domain-c9
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

        salt '*' vcf_vim_cluster_config.dpm_set domain-c9 enabled=true default_behavior=automated
    """
    return c.dpm_set(
        __opts__,
        cluster,
        enabled=enabled,
        default_behavior=default_behavior,
        host_power_action_rate=host_power_action_rate,
        profile=profile,
    )
