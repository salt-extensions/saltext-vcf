{% import_yaml "templates/log-forwarder-template.yaml" as cfg %}

vcenter-syslog:
  vcf_vcenter_appliance.logging_forwarding:
    - servers: {{ cfg.syslog.servers }}