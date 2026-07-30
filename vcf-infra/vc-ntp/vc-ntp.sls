{% from "vc-ntp/map.jinja" import cfg with context %}

vc-ntp:
  vcf_vcenter_appliances.ntp_servers:
    - servers: {{ cfg.ntp.servers }}
