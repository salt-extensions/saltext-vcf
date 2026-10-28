{% from "vc-patch/map.jinja" import cfg with context %}

vc-repo:
  vcf_vc_patch.repository_configured:
    - repository_url: {{ cfg.repository.url }}
    - auto_stage: {{ cfg.repository.auto_stage }}
    - certificate_check: {{ cfg.repository.certificate_check }}

vc-staged:
  vcf_vc_patch.update_prepared:
    - version: {{ cfg.version }}
    - require:
      - vcf_vc_patch: vc-repo

{% if cfg.get('install_enabled', false) %}
vc-installed:
  vcf_vc_patch.update_installed:
    - version: {{ cfg.version | tojson }}
    - sso_password: {{ cfg.sso_password | tojson }}
    - require:
      - vcf_vc_patch: vc-staged
{% endif %}
