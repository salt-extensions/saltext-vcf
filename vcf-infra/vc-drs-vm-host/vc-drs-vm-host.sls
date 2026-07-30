{% from "vc-drs-vm-host/map.jinja" import cfg with context %}

vcf_drs_vm_host:
  vcf_vim_drs_rule.vm_host:
    - name: {{ cfg.vm_host.name }}
    - cluster: {{ cfg.cluster.name }}
    - vm_group_name: {{ cfg.vm_host.vm_group_name }}
    - host_group_name: {{ cfg.vm_host.host_group_name }}
    - affine: {{ cfg.vm_host.affine }}
    - enabled: {{ cfg.vm_host.enabled }}
    - mandatory: {{ cfg.vm_host.mandatory }}
