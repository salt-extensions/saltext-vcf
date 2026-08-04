{% from "sddc-bringup/map.jinja" import cfg with context %}

vcf-bringup:
  vcf_installer_bringup.complete:
    - spec: {{ cfg.bringup.spec }}
    - wait: True
    - validate_first: True
