Added vSphere parity surface: ``vcf_vim_info.system_info`` (ServiceContent.about),
``vcf_vim_datastore`` (datastore get/list with VMFS detail, maintenance
mode, disk partition listing), folder rename/move (``vcf_vcenter_folder``
+ states), full DRS/HA knob surface in ``vcf_vim_cluster_config``
(advanced settings, VM Component Protection, tools monitoring, APD/PDL,
admission-control policy types, aggregate ``get_config``), full DVS
configure surface (discovery protocol, contact info, security policy,
health checks, uplink prefix, version update), per-host pnic detail on
``vcf_vim_dvs_portgroup.get``, license states
(``vcf_vim_license.present/absent``), tag states
(``vcf_vcenter_tag.present/absent``,
``vcf_vcenter_tag_category.present/absent``), and
``vcf_vcenter_datacenter.get_by_name`` / ``detail``.
