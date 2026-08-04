{% from "installer-depot/map.jinja" import cfg with context %}

vcf-installer-depot:
  module.run:
    - name: vcf_vcenter_lcm_depot.create_offline
    - file_locator: {{ cfg.depot.offline.file_locator }}
