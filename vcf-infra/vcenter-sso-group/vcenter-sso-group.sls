{% from "vcenter-sso-group/map.jinja" import cfg, group_id with context %}

{{ cfg.group.name }}:
  module.run:
    - name: vcf_vcenter_sso.groups_create
      # groups_create()'s first param is itself called "name", which collides
      # with module.run's own `name:` key (used above to select the function).
      # Salt's module.run state resolves this via the `m_name` convention.
    - m_name: {{ cfg.group.name }}
    - domain: {{ cfg.group.domain }}
    - description: {{ cfg.group.description }}
    - unless:
      - fun: vcf_vcenter_sso.groups_get_or_none
        group: {{ group_id }}
