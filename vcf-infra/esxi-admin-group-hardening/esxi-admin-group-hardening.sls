{% from "esxi-admin-group-hardening/map.jinja" import cfg with context %}

Config.HostAgent.plugins.hostsvc.esxAdminsGroupAutoAdd:
  vcf_esxi_advanced.setting:
    - value: {{ cfg.settings.esx_admins_group_auto_add | tojson }}

Config.HostAgent.plugins.vimsvc.authValidateInterval:
  vcf_esxi_advanced.setting:
    - value: {{ cfg.settings.auth_validate_interval | tojson }}

Config.HostAgent.plugins.hostsvc.esxAdminsGroup:
  vcf_esxi_advanced.setting:
    - value: {{ cfg.settings.esx_admins_group | tojson }}
