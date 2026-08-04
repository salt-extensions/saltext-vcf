{% from "vcenter-identity-source/map.jinja" import cfg with context %}

vcenter-identity-source:
  module.run:
    - name: vcf_vcenter_sso.providers_create
    - spec: {{ cfg.provider.spec }}
