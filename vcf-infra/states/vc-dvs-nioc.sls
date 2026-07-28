{% import_yaml "templates/vc-dvs-nioc-template.yaml" as cfg %}

{{ cfg.dvs.name }}:
  vcf_vcenter_dvs_nioc.nioc_enabled:
    - enabled: {{ cfg.dvs.nioc_enabled }}
