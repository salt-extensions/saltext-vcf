# Drive a complete VCF 9.x deploy onto a bare ESXi host using saltext-vcf modules:
#
#   1. push the VCF Installer OVA via pyVmomi (vcf_installer_appliance.running)
#   2. submit the bringup spec and wait for the management-domain SDDC to come
#      up (vcf_installer_bringup.complete)
#
# Pillar inputs (under ``saltext.vcf:``):
#
#   installer_appliance:
#     installer_host: <installer-fqdn>
#     installer_ova_url: <local-path-or-https-url>
#     installer_vm_name: <vm-name>
#     installer_deploy_esxi: <esxi-fqdn>
#     esxi_hosts:
#       - {fqdn: <esxi-fqdn>, username: root, password: <secret>}
#     # optional: datastore, network_map, ovf_properties, ...
#
#   bringup_spec: { ...VCF Installer SddcSpec JSON... }
#
# Run with (no Salt master required, file_roots must include this dir):
#
#   salt-call --local state.sls _orchestrate.vcf_deploy.full_stack

include:
  - _orchestrate.vcf_deploy.installer_appliance
  - _orchestrate.vcf_deploy.bringup
