{% from "vcenter-service/map.jinja" import cfg with context %}

{{ cfg.service.name }}:
  module.run:
    - name: vcf_vcenter_appliance.services_start
    - service: {{ cfg.service.name }}
