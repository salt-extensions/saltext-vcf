{% from "esxi-netdump/map.jinja" import cfg with context %}

esxi-netdump:
  vcf_esxi_netdump.configured:
    - interface_name: {{ cfg.netdump.interface_name }}
    - server_ip: {{ cfg.netdump.server_ip }}
    - server_port: {{ cfg.netdump.server_port }}
    - enabled: {{ cfg.netdump.enabled }}
