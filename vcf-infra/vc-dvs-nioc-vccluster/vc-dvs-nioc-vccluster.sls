{% from "vc-dvs-nioc-vccluster/map.jinja" import cfg with context %}

{{ cfg.name }}:
  vcf_vcenter_dvs_nioc_vccluster.nioc_enabled:
    - enabled: {{ cfg.nioc_enabled }}
