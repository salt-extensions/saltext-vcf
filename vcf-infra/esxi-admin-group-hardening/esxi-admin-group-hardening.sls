{# BEGIN-KB-METADATA
kb:
  - id: "369707"
    title: "ESXi host may grant unintended full administrative access to Active Directory group members"
    description: >-
      When an ESXi host is joined to Active Directory, all members of the
      group named "ESX Admins" (by default) are automatically granted full
      administrative access to the host. Fixed natively in ESXi 8.0 U3;
      this state applies the documented workaround for earlier releases by
      disabling the automatic group grant and shortening the permission
      re-validation interval. Settings take effect within a minute; no
      reboot is required. Does not perform the KB's separate manual step
      (removing a stale "ESX Admins" permission entry on a host that was
      already joined before this workaround was applied) -- see
      applicability.prerequisites in the matching KB solution entry.
    url: "https://broadcomcms-software-agent.wolkenservicedesk.com/wolken/esd/knowledge-base-view/view-kb-article?articleNumber=369707"
END-KB-METADATA #}

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
