{% import_yaml "templates/vc-dns-template.yaml" as cfg %}

vc-dns:
  vcf_vcenter_appliance.dns_servers:
    - servers: {{ cfg.dns.servers }}
