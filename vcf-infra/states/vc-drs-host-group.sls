{% import_yaml "templates/vc-drs-host-group-template.yaml" as cfg %}

vcf_drs_host_group:
  vcf_vim_drs_rule.host_group:
    - name: {{ cfg.host_group.name }}
    - cluster: {{ cfg.cluster.name }}
    - host_moids: {{ cfg.host_group.host_moids }}
