{% from "ops-patch/map.jinja" import cfg with context %}
{% set conn = cfg.connection %}

ops-health-precheck:
  vcf_ops_patch.cluster_health_validated:
    - host: {{ conn.host }}
    - username: {{ conn.username }}
    - password: {{ conn.password }}
    - protocol: {{ conn.protocol }}
    - port: {{ conn.port }}
    - verify_ssl: {{ conn.verify_ssl }}

ops-pak-downloaded:
  vcf_ops_patch.pak_downloaded:
    - host: {{ conn.host }}
    - username: {{ conn.username }}
    - password: {{ conn.password }}
    - protocol: {{ conn.protocol }}
    - port: {{ conn.port }}
    - verify_ssl: {{ conn.verify_ssl }}
    - pak_source: {{ cfg.pak.source }}
    - destination: {{ cfg.pak.destination }}
    - download_dir: {{ cfg.lifecycle.download_dir }}
    - download_timeout: {{ cfg.lifecycle.download_timeout_seconds }}
    - verify_download_ssl: {{ cfg.pak.verify_download_ssl }}
    - calculate_checksum: {{ cfg.pak.calculate_checksum }}
    {% if cfg.pak.checksum %}
    - checksum: {{ cfg.pak.checksum }}
    {% endif %}
    - require:
      - vcf_ops_patch: ops-health-precheck

ops-pak-installed:
  vcf_ops_patch.pak_installed:
    - host: {{ conn.host }}
    - username: {{ conn.username }}
    - password: {{ conn.password }}
    - protocol: {{ conn.protocol }}
    - port: {{ conn.port }}
    - verify_ssl: {{ conn.verify_ssl }}
    - pak_file: {{ cfg.pak.destination }}
    - pak_handling_advice: {{ cfg.pak.handling_advice }}
    - install_timeout: {{ cfg.lifecycle.install_timeout_seconds }}
    {% if cfg.pak.get('id') %}
    - pak_id: {{ cfg.pak.id }}
    {% endif %}
    - require:
      - vcf_ops_patch: ops-pak-downloaded

ops-upgrade-monitored:
  vcf_ops_patch.upgrade_monitored:
    - host: {{ conn.host }}
    - username: {{ conn.username }}
    - password: {{ conn.password }}
    - protocol: {{ conn.protocol }}
    - port: {{ conn.port }}
    - verify_ssl: {{ conn.verify_ssl }}
    - timeout_seconds: {{ cfg.lifecycle.upgrade_timeout_seconds }}
    - poll_interval_seconds: {{ cfg.lifecycle.poll_interval_seconds }}
    - max_transient_errors: {{ cfg.lifecycle.max_transient_errors }}
    {% if cfg.pak.get('id') %}
    - pak_id: {{ cfg.pak.id }}
    {% endif %}
    - require:
      - vcf_ops_patch: ops-pak-installed

ops-cluster-online:
  vcf_ops_patch.cluster_online_verified:
    - host: {{ conn.host }}
    - username: {{ conn.username }}
    - password: {{ conn.password }}
    - protocol: {{ conn.protocol }}
    - port: {{ conn.port }}
    - verify_ssl: {{ conn.verify_ssl }}
    - timeout_seconds: {{ cfg.lifecycle.cluster_online_timeout_seconds }}
    - poll_interval_seconds: {{ cfg.lifecycle.poll_interval_seconds }}
    - require:
      - vcf_ops_patch: ops-upgrade-monitored

ops-patch-report:
  vcf_ops_patch.reported:
    - host: {{ conn.host }}
    - username: {{ conn.username }}
    - password: {{ conn.password }}
    - protocol: {{ conn.protocol }}
    - port: {{ conn.port }}
    - verify_ssl: {{ conn.verify_ssl }}
    - require:
      - vcf_ops_patch: ops-cluster-online
