{% import_yaml "templates/vc-dvs-nioc-vccluster-template.yaml" as cfg %}

{{ cfg.cluster.name }}:
  vcf_vcenter_dvs_nioc_vccluster.nioc_enabled:
    - enabled: {{ cfg.cluster.nioc_enabled }}
