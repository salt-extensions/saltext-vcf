{% from "vc-advanced-option/map.jinja" import cfg with context %}

{{ cfg.advanced_option.key }}:
  vcf_vcenter_advanced_option.advanced_option:
    - value: {{ cfg.advanced_option.value }}
