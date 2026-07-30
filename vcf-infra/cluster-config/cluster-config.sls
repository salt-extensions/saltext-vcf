{% from "cluster-config/map.jinja" import cfg with context %}

vcf_cluster_config:
  vcf_cluster_config.profile_value:
    - name: {{ cfg.cluster.name }}
    - key: {{ cfg.profile.key }}
    - value: {{ cfg.profile.value }}
