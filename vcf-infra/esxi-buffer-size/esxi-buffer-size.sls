{% from "esxi-buffer-size/map.jinja" import cfg with context %}

{{ cfg.advanced.setting }}:
  vcf_esxi_advanced.setting:
    - value: {{ cfg.advanced.value }}
