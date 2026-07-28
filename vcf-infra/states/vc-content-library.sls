{% import_yaml "templates/vc-content-library-template.yaml" as cfg %}

{{ cfg.library.name }}:
  vcf_vcenter_content_library.present:
    - storage_backings: {{ cfg.storage_backings }}
