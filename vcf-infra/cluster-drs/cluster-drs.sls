{% from "cluster-drs/map.jinja" import cfg with context %}

vcf_cluster_drs:
  vcf_vim_cluster_config.drs:
    - cluster: {{ cfg.cluster.name }}
    - enabled: {{ cfg.drs.enabled }}
    - default_vm_behavior: {{ cfg.drs.default_vm_behavior }}
    - migration_threshold: {{ cfg.drs.migration_threshold }}
    - vm_monitoring_enabled: {{ cfg.drs.vm_monitoring_enabled }}
