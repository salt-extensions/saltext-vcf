{% import_yaml "templates/vc-advanced-option-template.yaml" as cfg %}

{{ cfg.advanced_option.key }}:
  vcf_vcenter_advanced_option.advanced_option:
    - value: {{ cfg.advanced_option.value }}
