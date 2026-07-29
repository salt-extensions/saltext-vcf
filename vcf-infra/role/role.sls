{% from "role/map.jinja" import cfg with context %}

{{ cfg.role.name }}:
  vcf_vim_role.present:
    - privileges: {{ cfg.role.privileges }}
