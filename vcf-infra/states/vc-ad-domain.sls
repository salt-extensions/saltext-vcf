{% import_yaml "templates/vc-ad-domain-template.yaml" as cfg %}

{{ cfg.ad_domain.name }}:
  vcf_vcenter_ad_domain.ad_joined:
    - username: {{ cfg.ad_domain.username }}
    - password: {{ cfg.ad_domain.password }}
