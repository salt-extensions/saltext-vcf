{% from "vcenter-nkp/map.jinja" import cfg with context %}

vcenter-nkp:
  module.run:
    - name: vcf_vcenter_kms.create
    - provider_spec: {{ cfg.kms.provider_spec }}
