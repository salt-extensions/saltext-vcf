{% from "vcenter-sso-group/map.jinja" import cfg with context %}

{{ cfg.group.name | tojson }}:
  vcf_vcenter_sso_group.present:
    - domain: {{ cfg.group.domain | tojson }}
    - description: {{ cfg.group.description | tojson }}
