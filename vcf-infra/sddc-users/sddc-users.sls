{% from "sddc-users/map.jinja" import cfg with context %}

sddc-users-add:
  module.run:
    - name: vcf_sddc_system.add_users
    - user_specs: {{ cfg.users.user_specs }}
