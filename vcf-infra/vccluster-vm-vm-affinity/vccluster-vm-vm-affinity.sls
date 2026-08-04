{% from "vccluster-vm-vm-affinity/map.jinja" import cfg with context %}

{{ cfg.rule.name }}:
  vcf_vim_drs_rule.vm_affinity:
    - cluster: {{ cfg.cluster.id }}
    - vm_moids: {{ cfg.rule.vm_moids }}
    - enabled: {{ cfg.rule.enabled }}
    - mandatory: {{ cfg.rule.mandatory }}
