{% from "vc-dns/map.jinja" import cfg with context %}

vc-dns:
  vcf_vcenter_appliance.dns_servers:
    - servers: {{ cfg.dns.servers }}
