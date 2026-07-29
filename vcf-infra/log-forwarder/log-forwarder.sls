{% from "log-forwarder/map.jinja" import cfg with context %}

vcenter-syslog:
  vcf_vcenter_appliance.logging_forwarding:
    - servers: {{ cfg.syslog.servers }}
