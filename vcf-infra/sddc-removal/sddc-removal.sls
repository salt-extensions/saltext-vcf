{% from "sddc-removal/map.jinja" import cfg with context %}

{{ cfg.host.fqdn }}:
  vcf_sddc_host.decommissioned: []

{{ cfg.domain.name }}:
  vcf_sddc_domain.absent:
    - require:
      - vcf_sddc_host: {{ cfg.host.fqdn }}
