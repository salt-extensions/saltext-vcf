{% from "permission-vccluster/map.jinja" import cfg with context %}

svc-automation-on-vccluster:
  vcf_vim_permission.present:
    - entity_ref: {{ cfg.entity_ref }}
    - principal: {{ cfg.principal }}
    - role: {{ cfg.role }}
    - propagate: {{ cfg.propagate }}
    - group: {{ cfg.group }}
