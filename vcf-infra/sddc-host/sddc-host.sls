{% from "sddc-host/map.jinja" import cfg with context %}

{{ cfg.host.fqdn }}:
  vcf_sddc_host.commissioned: []
