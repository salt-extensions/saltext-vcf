{% from "vcenter-identity-source/map.jinja" import cfg with context %}
{% set spec = cfg.provider.spec %}

{% if not spec.get('config_tag') %}
vcenter-identity-source:
  test.fail_without_changes:
    - name: "Configure provider.spec with a valid federation-provider config_tag and its required settings."
{% elif 'server_type' in spec or 'server_endpoints' in spec or 'domain_name' in spec %}
vcenter-identity-source:
  test.fail_without_changes:
    - name: "Invalid provider spec: remove top-level server_type, server_endpoints, and domain_name."
{% else %}
vcenter-identity-source:
  module.run:
    - name: vcf_vcenter_sso.providers_create
    - spec: {{ spec | tojson }}
{% endif %}
