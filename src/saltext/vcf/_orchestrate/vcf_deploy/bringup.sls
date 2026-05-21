# Stage 0: drive the VCF Installer REST API to bring up the management domain.
#
# ``vcf_installer_bringup.complete`` is idempotent against the installer's
# task list — if a bringup is already in progress or has completed, the state
# reuses it instead of resubmitting.

include:
  - _orchestrate.vcf_deploy.installer_appliance

ensure_management_domain_bringup_complete:
  vcf_installer_bringup.complete:
    - name: {{ pillar.get('saltext.vcf', {}).get('bringup_spec', {}).get('sddcId', 'mgmt-domain') }}
    - spec: {{ pillar.get('saltext.vcf', {}).get('bringup_spec', {}) | tojson }}
    - timeout: {{ pillar.get('saltext.vcf', {}).get('bringup_timeout', 14400) }}
    - require:
      - vcf_installer_appliance: ensure_vcf_installer_appliance
