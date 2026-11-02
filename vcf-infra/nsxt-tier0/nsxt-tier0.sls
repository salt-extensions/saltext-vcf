{% from "nsxt-tier0/map.jinja" import cfg with context %}

{{ cfg.tier0.name }}-bgp:
  vcf_nsx_tier0.bgp_enabled:
    - name: {{ cfg.tier0.name }}
    - enabled: {{ cfg.tier0.bgp_enabled }}
    - locale_service: {{ cfg.tier0.locale_service }}

{{ cfg.tier0.name }}-ospf:
  vcf_nsx_tier0.ospf_enabled:
    - name: {{ cfg.tier0.name }}
    - enabled: {{ cfg.tier0.ospf_enabled }}
    - locale_service: {{ cfg.tier0.locale_service }}

{{ cfg.tier0.name }}-multicast:
  vcf_nsx_tier0.multicast_enabled:
    - name: {{ cfg.tier0.name }}
    - enabled: {{ cfg.tier0.multicast_enabled }}
    - locale_service: {{ cfg.tier0.locale_service }}
