{% from "vc-dvs-nioc/map.jinja" import cfg with context %}

{{ cfg.dvs.name }}:
  vcf_vcenter_dvs_nioc.nioc_enabled:
    - enabled: {{ cfg.dvs.nioc_enabled }}
