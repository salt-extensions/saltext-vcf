{% from "vc-dvs-nioc/map.jinja" import cfg with context %}

{{ cfg.name }}:
  vcf_vcenter_dvs_nioc.nioc_enabled:
    - enabled: {{ cfg.nioc_enabled }}
