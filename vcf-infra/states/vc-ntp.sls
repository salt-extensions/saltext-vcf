{% import_yaml "templates/vc-ntp-template.yaml" as cfg %}

vc-ntp:
  vcf_vcenter_appliances.ntp_servers:
    - servers: {{ cfg.ntp.servers }}
