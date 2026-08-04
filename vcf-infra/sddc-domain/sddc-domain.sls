{% from "sddc-domain/map.jinja" import cfg with context %}

{{ cfg.domain.name }}:
  vcf_sddc_domain.present:
    - spec: {{ cfg.domain.spec }}
