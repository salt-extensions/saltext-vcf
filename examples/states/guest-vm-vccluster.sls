{% import_yaml "templates/guest-vm-vccluster-template.yaml" as cfg %}

{{ cfg.vm.name }}:
  vcf_vim_vm.present:
    - host: {{ cfg.placement.esxi_host }}
    - datastore: {{ cfg.placement.datastore }}
    - cpu_count: {{ cfg.hardware.cpu_count }}
    - memory_mb: {{ cfg.hardware.memory_mb }}
    - guest_id: {{ cfg.vm.guest_id }}
    - disks:
      - size_gb: {{ cfg.storage.disk_size_gb }}
    - nics:
      - network: {{ cfg.network.portgroup }}