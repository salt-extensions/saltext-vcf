{% from "mgmt-components-upgrade/map.jinja" import cfg with context %}
{% set conn = cfg.connection %}
{% set up = cfg.upgrade %}

mgmt-components-upgrade-ready:
  vcf_mgmt_components_upgrade.ready_validated:
    - host: {{ conn.host }}
    - ops_host: {{ conn.ops_host }}
    - username: {{ conn.username }}
    - password: {{ conn.password }}
    - verify_ssl: {{ conn.verify_ssl }}
    {% if up.target_version %}
    - target_version: {{ up.target_version }}
    {% endif %}
    {% if up.plan_id %}
    - plan_id: {{ up.plan_id }}
    {% endif %}
    {% if up.order %}
    - order: {{ up.order | json }}
    {% endif %}

mgmt-components-upgrade-plan-configured:
  vcf_mgmt_components_upgrade.plan_configured:
    - host: {{ conn.host }}
    - ops_host: {{ conn.ops_host }}
    - username: {{ conn.username }}
    - password: {{ conn.password }}
    - verify_ssl: {{ conn.verify_ssl }}
    {% if up.target_version %}
    - target_version: {{ up.target_version }}
    {% endif %}
    {% if up.plan_id %}
    - plan_id: {{ up.plan_id }}
    {% endif %}
    {% if up.order %}
    - order: {{ up.order | json }}
    {% endif %}
    - timeout_seconds: {{ up.plan_timeout_seconds }}
    - poll_interval_seconds: {{ up.poll_interval_seconds }}
    - require:
      - vcf_mgmt_components_upgrade: mgmt-components-upgrade-ready

mgmt-components-upgrade-applied:
  vcf_mgmt_components_upgrade.upgrade_applied:
    - host: {{ conn.host }}
    - ops_host: {{ conn.ops_host }}
    - username: {{ conn.username }}
    - password: {{ conn.password }}
    - verify_ssl: {{ conn.verify_ssl }}
    {% if up.target_version %}
    - target_version: {{ up.target_version }}
    {% endif %}
    {% if up.plan_id %}
    - plan_id: {{ up.plan_id }}
    {% endif %}
    {% if up.order %}
    - order: {{ up.order | json }}
    {% endif %}
    - timeout_seconds: {{ up.apply_timeout_seconds }}
    - poll_interval_seconds: {{ up.poll_interval_seconds }}
    - require:
      - vcf_mgmt_components_upgrade: mgmt-components-upgrade-plan-configured

mgmt-components-upgrade-report:
  vcf_mgmt_components_upgrade.reported:
    - host: {{ conn.host }}
    - ops_host: {{ conn.ops_host }}
    - username: {{ conn.username }}
    - password: {{ conn.password }}
    - verify_ssl: {{ conn.verify_ssl }}
    - require:
      - vcf_mgmt_components_upgrade: mgmt-components-upgrade-applied
