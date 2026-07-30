{% from "vc-custom-attribute/map.jinja" import cfg with context %}

{{ cfg.custom_attribute.name }}:
  vcf_vcenter_custom_attribute.present:
    - managed_object_type: {{ cfg.custom_attribute.managed_object_type }}
