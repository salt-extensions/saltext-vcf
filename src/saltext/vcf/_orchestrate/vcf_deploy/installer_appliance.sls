# Stage -1b: deploy the VCF Installer OVA onto a bare ESXi host.
#
# Idempotent: if installer_host:installer_port already accepts a TCP
# connection, no OVA is pushed.

ensure_vcf_installer_appliance:
  vcf_installer_appliance.running:
    - name: {{ pillar.get('saltext.vcf', {}).get('installer_appliance', {}).get('installer_host', 'vcf-installer') }}
