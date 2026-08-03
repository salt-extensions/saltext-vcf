{% from "vc-custom-attribute/map.jinja" import cfg with context %}

{{ cfg.name }}:
  vcf_vcenter_custom_attribute.present:
    - managed_object_type: {{ cfg.managed_object_type }}
