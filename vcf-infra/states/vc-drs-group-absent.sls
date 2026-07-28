{% import_yaml "templates/vc-drs-group-absent-template.yaml" as cfg %}

vcf_drs_group_absent:
  vcf_vim_drs_rule.group_absent:
    - name: {{ cfg.group.name }}
    - cluster: {{ cfg.cluster.name }}
