{% from "vc-content-library/map.jinja" import cfg with context %}

{{ cfg.library.name }}:
  vcf_vcenter_content_library.present:
    - storage_backings: {{ cfg.storage_backings }}
