# vSphere parity with saltext-vmware

saltext-vcf covers the VCF stack REST-first, using SOAP (pyVmomi) only
where vCenter's REST API has no surface. The `saltext.vmware`
extension is SOAP-first. This ledger tracks the function-level parity
work that ported missing / partial `saltext.vmware` vSphere surface
into saltext-vcf's conventions (client → exec module → state, `vcf_*`
virtual names, `opts`/`profile=` instead of `service_instance`).

## Parity ledger

### VM (vmware_vm → vcf_vim_vm*)

| source function | status | saltext-vcf surface |
|---|---|---|
| `list_` | covered (pre-existing) | `vcf_vcenter_vm.list_` / `.search` |
| `list_templates` | **ported** | `vcf_vim_vm.list_templates` |
| `path` | **ported** | `vcf_vim_vm.path` |
| `info` | **ported** | `vcf_vim_vm.info` (guest IPs, MACs, uuid, vmPathName) |
| `deploy_ovf` | **ported** | `vcf_vcenter_vm.deploy_ovf` (raw OVF/OVF-dir support in `clients/ovf_deploy`) |
| `deploy_ova` | covered | `vcf_vcenter_vm.deploy_ova` (pyvmomi / ovftool backends) |
| `deploy_template` | covered (pre-existing) | `vcf_vim_vm.clone` |
| `power_state` | covered (pre-existing) | `vcf_vim_vm_power.*` |
| `boot_manager` | **ported** | `vcf_vim_vm_boot.get/set` (boot order incl. `bootOrder` device classes, retry, EFI secure boot) |
| `get_mks_ticket` | **ported** | `vcf_vim_vm_console.get_ticket` |
| `create/destroy/snapshot` | covered (pre-existing) | `vcf_vim_vm_snapshot.*` |
| `relocate` | covered (pre-existing) | `vcf_vim_vm_migrate.relocate` |
| `register` | covered (pre-existing) | `vcf_vim_vm.register` |
| `register_all` | **ported** | `vcf_vim_vm.register_all` (+ `vim_datastore_file.find_vmx`) |
| `unregister` | **upgraded** | `vcf_vim_vm.unregister` gained `shutdown=` graceful pre-step |
| `unregister_all` | **ported** | `vcf_vim_vm.unregister_all` |
| `set_ip_info` | **ported** | `vcf_vim_vm_customization.set_ip_info` (Linux/Windows identity, single-NIC guard) |
| `set_dvport` | **upgraded** | `vcf_vim_vm_nic.set_dvport` resolves DVS/DPG **by name** |

New state modules: `vcf_vim_vm_boot.boot_manager`,
`vcf_vim_vm_snapshot.present/absent`, `vcf_vim_vm_migrate.relocate`.

### ESXi host (vmware_esxi → vcf_vim_host* / vcf_esxi*)

| source function | status | saltext-vcf surface |
|---|---|---|
| `get_lun_ids` / `get_host_disks` | **ported** | `vcf_vim_host_datastore.lun_ids` / `.disks` |
| `list_scsi_luns` / `list_disks` | **ported (full)** | `vcf_vim_host_storage.scsi_luns` (full ScsiLun dump + filters) |
| `list_diskgroups` | covered (pre-existing) | `vcf_vsan_disk.host_disk_mapping` |
| `get_capabilities` | **ported** | `vcf_vim_host.capabilities` |
| `power_state` | **upgraded** | `vcf_vim_host.power_state` (reboot/shutdown/standby/poweron + task wait) |
| `rescan_storage` | covered (pre-existing) | `vcf_vim_host_storage.refresh/rescan_all_hba` |
| `mount/unmount_storage` | **ported** | `vcf_vim_host_storage.attach_lun` / `.detach_lun` |
| services / acceptance level / advanced / DNS / NTP / AD / users / roles / maintenance / lockdown / vSAN | covered (pre-existing) | `vcf_vim_host_config.*`, `vcf_vim_host_acceptance.*`, `vcf_vim_host_security.*`, `vcf_vim_role.*`, `vcf_vim_host_maintenance.*`, `vcf_vsan_*` |
| `backup_config` / `restore_config` / `reset_config` | **ported** | `vcf_vim_host_firmware.backup/restore/reset` |
| `list_pkgs` | **ported** | `vcf_vim_host_packages.list_` |
| `get_host_datetime` | **ported** | `vcf_vim_host_config.datetime_get` |
| `get_ntp_config` | **upgraded** | `ntp_get` now reports `time_zone` + `config_file` |
| `set_advanced_configs` | **upgraded** | `vcf_vim_host_config.advanced_set_many` (multi-key + type coercion) |
| `connect` / `disconnect` / `remove` / `move` / `add` | **ported** | `vcf_vim_host.reconnect/disconnect/remove/move/add` |
| `get` (aggregator) | **ported** | `vcf_vim_host.info` (key/default/delimiter traversal) |
| firewall get/set incl. `ip_network` | **ported** | `vcf_vim_host_firewall.*` (vCenter-routed; standalone variant stays in `vcf_esxi_firewall`) |
| `create/update_vmkernel_adapter` | **upgraded** | `vcf_vim_host_network.vmkernel_add/update` (DVS portgroup binding, TCP/IP stack, per-adapter gateway, vSAN wiring, `vSphereReplicationNFC`) |
| `get_vmotion_enabled` / `vmotion_enable/disable` | **ported** | `vcf_vim_host_vmotion.*` (dedicated `HostVMotionSystem` surface) |
| `vsan_enable` (per-host) | **ported** | `vcf_vsan_disk.host_enable` |
| `get_user` | **upgraded** | `vcf_vim_host_security.user_get` / `user_list` now query the **host-local** directory (was vCenter SSO) |

New state modules: `vcf_vim_host_security` (`user_present`,
`user_absent`, `password_present`, `lockdown`),
`vcf_vim_host_maintenance.maintenance`, `vcf_vim_host_firewall`
(`firewall_config`, `firewall_configs` with drift reporting),
`vcf_vim_host_network.vmotion_configured` + upgraded
`vmkernel_present`, `vcf_vsan_disk.host_configured`, and
`vcf_vim_host_config.advanced_setting` now accepts a batch ``configs``
dict.

### Misc vSphere

| source function | status | saltext-vcf surface |
|---|---|---|
| `system_info` | **ported** | `vcf_vim_info.system_info` (`ServiceContent.about`) |
| `list_ssds` / `list_non_ssds` | **ported** | `vcf_vim_host_storage.list_ssds` / `.list_non_ssds` |
| datastore maintenance / full get / filtered list | **ported** | `vcf_vim_datastore.get/list_/maintenance_mode/exit_maintenance_mode` |
| `mount_datastore` / `unmount_datastore` (uuid-based remount) | **ported** | `vcf_vim_host_datastore.mount_vmfs` / `.unmount_vmfs` (incl. unresolved-uuid resolution) |
| `list_disk_partitions` | **ported** | `vcf_vim_datastore.list_disk_partitions` |
| folder `rename` / `move` | **ported** | `vcf_vcenter_folder.rename/move` + states `renamed`/`moved` |
| DRS `configure` (advanced settings, friendly `vmotion_rate`) | **upgraded** | `vcf_vim_cluster_config.drs_set/get` (`advanced_settings`, `vmotion_rate` = `6 - vmotionRate`) |
| HA `configure` (full `ConfigSpecEx` surface) | **upgraded** | `vcf_vim_cluster_config.ha_set/get` (VM Component Protection, tools-monitoring, restart-priority timeout, APD/PDL, admission-control policy types incl. failover-hosts / resource %, advanced options; no `defaultVmSettings` clobber) |
| cluster `get` aggregate | **ported** | `vcf_vim_cluster_config.get_config` (DRS + HA + vSAN in one call) |
| DVS `configure` (discovery, contact, security, health checks, uplink prefix, version update) | **upgraded** | `vcf_vim_dvs.create/reconfigure` |
| dvportgroup `get` (per-host pnics) | **upgraded** | `vcf_vim_dvs_portgroup.get(..., host=...)` |
| license states | **ported** | `vcf_vim_license.present/absent` (+ `resolve_entity` / `assign_by_name`) |
| tag states | **ported** | `vcf_vcenter_tag.present/absent`, `vcf_vcenter_tag_category.present/absent` (+ `by_name` resolvers) |
| datacenter `get` (by name + folders) | **upgraded** | `vcf_vcenter_datacenter.get_by_name` / `.detail` |

## Known deviations

* Client-layer functions take ``(opts, ...)`` and ``profile=`` instead
  of passing a ``service_instance`` around — the target's connection
  cache handles session reuse (parallel-safe states clear the cache).
* `vcf_vim_vm.register_all` registers every `*.vmx` found under the
  datastore root (recursive browser search); the source's
  datacenter/pool ambiguity guard is replaced by explicit placement
  args (`cluster=` / `host=` / `resource_pool=`).
* Boot-order entries whose device class is absent are skipped rather
  than raising (re-apply of an existing order never breaks).
* `vcf_vim_host_storage.detach_lun` implements the real
  `DetachScsiLun` API (the source's `unmount_storage` was a stub).
