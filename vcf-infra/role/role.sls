{% from "role/map.jinja" import cfg with context %}

{{ cfg.name }}:
  vcf_vim_role.present:
    - privileges: {{ cfg.privileges }}
