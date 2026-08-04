{% from "vc-drs-group-absent/map.jinja" import cfg with context %}

vcf_drs_group_absent:
  vcf_vim_drs_rule.group_absent:
    - name: {{ cfg.group.name }}
    - cluster: {{ cfg.cluster.name }}
