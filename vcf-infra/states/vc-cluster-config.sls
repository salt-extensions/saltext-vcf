{% import_yaml "templates/vc-cluster-config-template.yaml" as cfg %}

vcf_cluster_config:
  vcf_cluster_config.profile_value:
    - name: {{ cfg.cluster.name }}
    - key: {{ cfg.profile.key }}
    - value: {{ cfg.profile.value }}
