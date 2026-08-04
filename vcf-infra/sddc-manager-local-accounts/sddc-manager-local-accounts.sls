{% from "sddc-manager-local-accounts/map.jinja" import cfg with context %}

sddc-local-accounts:
  vcf_sddc_manager_local_accounts.audited:
    - expected_usernames: {{ cfg.expected_usernames }}
