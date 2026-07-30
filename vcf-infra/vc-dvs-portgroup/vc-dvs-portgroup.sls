{% from "vc-dvs-portgroup/map.jinja" import cfg with context %}

# Mutually exclusive examples — apply one or the other for a given portgroup.

{{ cfg.portgroup.name }}:
  vcf_vim_dvs.portgroup_present:
    - dvs: {{ cfg.dvs.name }}
    - vlan_id: {{ cfg.portgroup.vlan_id }}
    - num_ports: {{ cfg.portgroup.num_ports }}
    - binding: {{ cfg.portgroup.binding }}
    - promiscuous: {{ cfg.portgroup.promiscuous }}

{{ cfg.portgroup.name }}-absent:
  vcf_vim_dvs.portgroup_absent:
    - name: {{ cfg.portgroup.name }}
    - dvs: {{ cfg.dvs.name }}
