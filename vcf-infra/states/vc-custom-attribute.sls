{% import_yaml "templates/vc-custom-attribute-template.yaml" as cfg %}

{{ cfg.custom_attribute.name }}:
  vcf_vcenter_custom_attribute.present:
    - managed_object_type: {{ cfg.custom_attribute.managed_object_type }}
