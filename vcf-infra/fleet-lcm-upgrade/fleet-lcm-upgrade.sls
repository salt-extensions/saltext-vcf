{% from "fleet-lcm-upgrade/map.jinja" import cfg with context %}
{% set conn = cfg.connection %}
{% set up = cfg.upgrade %}

fleet-lcm-ready:
  vcf_fleet_lcm.ready_validated:
    - host: {{ conn.host }}
    - ops_host: {{ conn.ops_host }}
    - username: {{ conn.username }}
    - password: {{ conn.password }}
    - verify_ssl: {{ conn.verify_ssl }}
    {% if up.target_version %}
    - target_version: {{ up.target_version }}
    {% endif %}

fleet-lcm-plan-configured:
  vcf_fleet_lcm.plan_configured:
    - host: {{ conn.host }}
    - ops_host: {{ conn.ops_host }}
    - username: {{ conn.username }}
    - password: {{ conn.password }}
    - verify_ssl: {{ conn.verify_ssl }}
    {% if up.target_version %}
    - target_version: {{ up.target_version }}
    {% endif %}
    - timeout_seconds: {{ up.plan_timeout_seconds }}
    - poll_interval_seconds: {{ up.poll_interval_seconds }}
    - require:
      - vcf_fleet_lcm: fleet-lcm-ready

fleet-lcm-upgrade-applied:
  vcf_fleet_lcm.upgrade_applied:
    - host: {{ conn.host }}
    - ops_host: {{ conn.ops_host }}
    - username: {{ conn.username }}
    - password: {{ conn.password }}
    - verify_ssl: {{ conn.verify_ssl }}
    {% if up.target_version %}
    - target_version: {{ up.target_version }}
    {% endif %}
    - timeout_seconds: {{ up.apply_timeout_seconds }}
    - poll_interval_seconds: {{ up.poll_interval_seconds }}
    - require:
      - vcf_fleet_lcm: fleet-lcm-plan-configured

fleet-lcm-report:
  vcf_fleet_lcm.reported:
    - host: {{ conn.host }}
    - ops_host: {{ conn.ops_host }}
    - username: {{ conn.username }}
    - password: {{ conn.password }}
    - verify_ssl: {{ conn.verify_ssl }}
    - require:
      - vcf_fleet_lcm: fleet-lcm-upgrade-applied
