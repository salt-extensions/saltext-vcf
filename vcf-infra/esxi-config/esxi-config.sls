{% from "esxi-config/map.jinja" import cfg with context %}

esxi-ntp:
  vcf_esxi_ntp.servers:
    - servers: {{ cfg.ntp.servers }}
    - enabled: {{ cfg.ntp.enabled }}

{{ cfg.advanced.setting }}:
  vcf_esxi_advanced.setting:
    - value: {{ cfg.advanced.value }}

esxi-syslog:
  vcf_esxi_syslog.servers:
    - servers: {{ cfg.syslog.servers }}
    - log_level: {{ cfg.syslog.log_level }}

{{ cfg.service.name }}:
  vcf_esxi_service.running:
    - policy: "{{ cfg.service.policy }}"

{{ cfg.firewall.rule }}:
  vcf_esxi_firewall.rule_enabled:
    - enabled: {{ cfg.firewall.enabled }}
    - allowed_ips: {{ cfg.firewall.allowed_ips }}
    - all_ip: {{ cfg.firewall.all_ip }}

esxi-dns:
  vcf_vim_host_dns.config:
    - host: {{ cfg.dns.host }}
    - dhcp: {{ cfg.dns.dhcp }}
    - hostname: {{ cfg.dns.hostname }}
    - domain_name: {{ cfg.dns.domain_name }}
    - servers: {{ cfg.dns.servers }}
    - search_domains: {{ cfg.dns.search_domains }}
