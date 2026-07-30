{% from "vc-drs-host-group/map.jinja" import cfg with context %}

vcf_drs_host_group:
  vcf_vim_drs_rule.host_group:
    - name: {{ cfg.host_group.name }}
    - cluster: {{ cfg.cluster.name }}
    - host_moids: {{ cfg.host_group.host_moids }}
