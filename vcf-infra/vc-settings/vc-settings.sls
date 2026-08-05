{#
  vcenter_settings (Ansible item #73) maps to a curated subset of vCenter
  Server's own advanced settings (config.vpxd.* keys) -- the exact
  mechanism item #47 (vcenter_advanced_option) already manages generically
  via vcf_vcenter_advanced_option. No new module was needed; this example
  just applies the specific keys this Ansible role touches.

  Deliberately NOT covered here: "database" and "runtime_settings" (no
  confirmed advanced-option key mapping without checking a live vpxd.cfg)
  and "user_directory" (that's vCenter SSO identity sources, already
  covered by item #64 / vc-content of vcenter-identity-source/). Confirm
  the exact keys against a real vCenter's Advanced Settings page before
  relying on this for those three.
#}
{% from "vc-settings/map.jinja" import cfg with context %}

vc-settings-log-level:
  vcf_vcenter_advanced_option.advanced_option:
    - name: config.log.level
    - value: {{ cfg.settings.logging_options.level }}

vc-settings-mail-server:
  vcf_vcenter_advanced_option.advanced_option:
    - name: mail.smtp.server
    - value: {{ cfg.settings.mail.server }}

vc-settings-mail-sender:
  vcf_vcenter_advanced_option.advanced_option:
    - name: mail.sender
    - value: {{ cfg.settings.mail.sender }}

vc-settings-timeout-normal:
  vcf_vcenter_advanced_option.advanced_option:
    - name: client.timeout.normal
    - value: {{ cfg.settings.timeout_settings.normal_seconds }}

vc-settings-timeout-long:
  vcf_vcenter_advanced_option.advanced_option:
    - name: client.timeout.long
    - value: {{ cfg.settings.timeout_settings.long_seconds }}

{% for receiver in cfg.settings.snmp_receivers %}
vc-settings-snmp-receiver-{{ loop.index }}-enabled:
  vcf_vcenter_advanced_option.advanced_option:
    - name: snmp.receiver.{{ loop.index }}.enabled
    - value: {{ receiver.enabled }}

vc-settings-snmp-receiver-{{ loop.index }}-name:
  vcf_vcenter_advanced_option.advanced_option:
    - name: snmp.receiver.{{ loop.index }}.name
    - value: {{ receiver.name }}

vc-settings-snmp-receiver-{{ loop.index }}-port:
  vcf_vcenter_advanced_option.advanced_option:
    - name: snmp.receiver.{{ loop.index }}.port
    - value: {{ receiver.port }}

vc-settings-snmp-receiver-{{ loop.index }}-community:
  vcf_vcenter_advanced_option.advanced_option:
    - name: snmp.receiver.{{ loop.index }}.community
    - value: {{ receiver.community }}
{% endfor %}
