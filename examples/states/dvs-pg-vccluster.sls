{% import_yaml "templates/dvs-pg-vccluster-template.yaml" as cfg %}

{{ cfg.portgroup.name }}:
  vcf_vim_dvs.portgroup_present:
    - dvs: {{ cfg.dvs.name }}
    - vlan_id: {{ cfg.portgroup.vlan_id }}
    - num_ports: {{ cfg.portgroup.num_ports }}
    - binding: {{ cfg.portgroup.binding }}