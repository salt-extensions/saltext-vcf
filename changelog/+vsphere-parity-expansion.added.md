Expanded the vSphere parity surface: per-host vSAN wiring
(``vim_host_network.vmkernel_vsan``), full ScsiLun inventory with
attach/detach LUN, VMFS extents + mount/unmount by uuid with
unresolved-volume resolution, firmware backup/restore/reset, VIB
package listing, host datetime, DVS-bound VMkernel adapters with
TCP/IP stacks and per-adapter gateways, firewall rulesets
(vCenter-routed) with ip_network support, vMotion interface
management, host lifecycle (reconnect/disconnect/remove/move/add),
capabilities and the info aggregator, boot-order management
(``vim_vm_boot``), MKS tickets, register/unregister_all, raw-OVF
deploy support, set_ip_info, set_dvport by name, folder rename/move,
full DRS/HA knob surface (admission-control policies, APD/PDL,
advanced settings), datastore maintenance/partitions, license and
tag states. New states: user/password/lockdown, maintenance,
firewall, vmotion_configured, boot_manager, snapshot, relocate,
license, tag, datastore maintenance. See
``docs/topics/vsphere-parity.md`` for the function-level ledger.
