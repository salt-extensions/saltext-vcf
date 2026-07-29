{% from "dvs-pg-vccluster/map.jinja" import cfg with context %}

{{ cfg.portgroup.name }}:
  vcf_vim_dvs.portgroup_present:
    - dvs: {{ cfg.dvs.name }}
    - vlan_id: {{ cfg.portgroup.vlan_id }}
    - num_ports: {{ cfg.portgroup.num_ports }}
    - binding: {{ cfg.portgroup.binding }}
