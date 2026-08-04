{% from "vc-drs-vm-group/map.jinja" import cfg with context %}

vcf_drs_vm_group:
  vcf_vim_drs_rule.vm_group:
    - name: {{ cfg.vm_group.name }}
    - cluster: {{ cfg.cluster.name }}
    - vm_moids: {{ cfg.vm_group.vm_moids }}
