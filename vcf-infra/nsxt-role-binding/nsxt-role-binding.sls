{% from "nsxt-role-binding/map.jinja" import cfg with context %}

{{ cfg.binding.name }}:
  vcf_nsx_role_binding.present:
    - type_: {{ cfg.binding.type }}
    - roles: {{ cfg.binding.roles }}
