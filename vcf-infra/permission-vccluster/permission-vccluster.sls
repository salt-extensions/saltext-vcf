{% from "permission-vccluster/map.jinja" import cfg with context %}

svc-automation-on-vccluster:
  vcf_vim_permission.present:
    - entity_ref: {{ cfg.permission.entity_ref }}
    - principal: {{ cfg.permission.principal }}
    - role: {{ cfg.permission.role }}
    - propagate: {{ cfg.permission.propagate }}
    - group: {{ cfg.permission.group }}
