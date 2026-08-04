{% from "nsxt-firewall-policy/map.jinja" import cfg with context %}

{{ cfg.policy.name }}:
  vcf_nsx_security_policy.present:
    - domain: {{ cfg.domain }}
    - category: {{ cfg.policy.spec.category }}
    - sequence_number: {{ cfg.policy.spec.sequence_number }}

{{ cfg.rule.name }}:
  vcf_nsx_firewall_rule.present:
    - policy: {{ cfg.policy.name }}
    - domain: {{ cfg.domain }}
    - action: {{ cfg.rule.spec.action }}
    - source_groups: {{ cfg.rule.spec.source_groups }}
    - destination_groups: {{ cfg.rule.spec.destination_groups }}
    - services: {{ cfg.rule.spec.services }}
    - scope: {{ cfg.rule.spec.scope }}
    - require:
      - vcf_nsx_security_policy: {{ cfg.policy.name }}
