{% from "esxi-localsh/map.jinja" import cfg with context %}

esxi-localsh:
  vcf_esxi_localsh.managed:
    - features: {{ cfg.localsh.features }}
    - execute: {{ cfg.localsh.execute }}
