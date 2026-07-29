{% import_yaml "templates/permission-template.yaml" as cfg %}

svc-automation-on-root:
  vcf_vim_permission.present:
    - entity_ref: {{ cfg.permission.entity_ref }}
    - principal: {{ cfg.permission.principal }}
    - role: {{ cfg.permission.role }}
    - propagate: {{ cfg.permission.propagate }}
    - group: {{ cfg.permission.group }}