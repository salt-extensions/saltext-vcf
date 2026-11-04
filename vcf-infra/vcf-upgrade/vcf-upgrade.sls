{% from "vcf-upgrade/map.jinja" import cfg with context %}

vcf-upgrade:
{% if cfg.sequence is not none %}
  vcf_upgrade.sequence_completed:
    - components: {{ cfg.sequence | tojson }}
{% else %}
  vcf_upgrade.upgraded:
    - component_type: {{ cfg.component_type | tojson }}
    - options: {{ cfg.options | tojson }}
{% endif %}
    - target_version: {{ (cfg.target_build or cfg.target_version) | tojson }}
    - domain_id: {{ cfg.domain_id | tojson }}
    - checkpoint_file: {{ cfg.checkpoint_file | tojson }}
    - profile: {{ cfg.profile | tojson }}
