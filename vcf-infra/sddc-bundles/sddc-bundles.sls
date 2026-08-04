{% from "sddc-bundles/map.jinja" import cfg with context %}

sddc-bundle-upload:
  module.run:
    - name: vcf_sddc_bundles.upload
    - bundle_file_path: {{ cfg.bundle.bundle_file_path }}
    - manifest_file_path: {{ cfg.bundle.manifest_file_path }}
    - signature_file_path: {{ cfg.bundle.signature_file_path }}
