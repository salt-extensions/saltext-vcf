Added ESXi-host parity surface: ``vcf_vim_host`` (reconnect, disconnect,
remove, move, add, power_state incl. standby, capabilities, info
aggregator), ``vcf_vim_host_firmware`` (backup/restore/reset),
``vcf_vim_host_packages``, ``vcf_vim_host_firewall`` (vCenter-routed
rulesets incl. ip_network), ``vcf_vim_host_vmotion``; extended
``vcf_vim_host_storage`` (full ScsiLun inventory, attach/detach LUN),
``vcf_vim_host_datastore`` (VMFS extents, mount/unmount by uuid with
unresolved-volume resolution), ``vcf_vim_host_config`` (host datetime,
NTP timezone, batch advanced settings with type coercion),
``vcf_vim_host_network`` (DVS-bound VMkernel adapters, TCP/IP stacks,
per-adapter gateway, vSAN wiring), ``vcf_vim_host_security``
(host-local user directory, ``user_get``), and ``vcf_vsan_disk``
(per-host vSAN enable). New states: ``vcf_vim_host_security``
(user/password/lockdown), ``vcf_vim_host_maintenance.maintenance``,
``vcf_vim_host_firewall.firewall_config(s)``,
``vcf_vim_host_network.vmotion_configured``, and
``vcf_vsan_disk.host_configured``.
