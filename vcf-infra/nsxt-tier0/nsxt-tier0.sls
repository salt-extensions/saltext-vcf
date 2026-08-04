{% from "nsxt-tier0/map.jinja" import cfg with context %}

{{ cfg.tier0.name }}:
  vcf_nsx_tier0.bgp_enabled:
    - enabled: {{ cfg.tier0.bgp_enabled }}
    - locale_service: {{ cfg.tier0.locale_service }}
  vcf_nsx_tier0.ospf_enabled:
    - enabled: {{ cfg.tier0.ospf_enabled }}
    - locale_service: {{ cfg.tier0.locale_service }}
  vcf_nsx_tier0.multicast_enabled:
    - enabled: {{ cfg.tier0.multicast_enabled }}
    - locale_service: {{ cfg.tier0.locale_service }}
