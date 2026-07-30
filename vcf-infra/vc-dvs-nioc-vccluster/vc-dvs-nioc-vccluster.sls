{% from "vc-dvs-nioc-vccluster/map.jinja" import cfg with context %}

{{ cfg.cluster.name }}:
  vcf_vcenter_dvs_nioc_vccluster.nioc_enabled:
    - enabled: {{ cfg.cluster.nioc_enabled }}
