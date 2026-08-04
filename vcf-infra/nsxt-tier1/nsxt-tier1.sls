{% from "nsxt-tier1/map.jinja" import cfg with context %}

{{ cfg.tier1.name }}:
  vcf_nsx_tier1.multicast_enabled:
    - enabled: {{ cfg.tier1.multicast_enabled }}
    - locale_service: {{ cfg.tier1.locale_service }}
