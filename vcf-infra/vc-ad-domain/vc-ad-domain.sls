{% from "vc-ad-domain/map.jinja" import cfg with context %}

{{ cfg.name }}:
  vcf_vcenter_ad_domain.ad_joined:
    - username: {{ cfg.username }}
    - password: {{ cfg.password }}
