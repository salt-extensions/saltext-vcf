{% from "vc-localos-user/map.jinja" import cfg with context %}

{{ cfg.user.username }}:
  vcf_vcenter_localos_user.present:
    - password: {{ cfg.user.password }}
    - roles: {{ cfg.user.roles }}
    - email: {{ cfg.user.email }}
    - full_name: {{ cfg.user.full_name }}
    - enabled: {{ cfg.user.enabled }}
