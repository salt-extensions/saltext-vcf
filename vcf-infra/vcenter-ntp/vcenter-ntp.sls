{# BEGIN-KB-METADATA
kb:
  - id: "313945"
    title: "How to configure NTP on vCenter Server Appliance (VCSA)"
    description: >-
      VCSA appliance-level NTP never set or configured via the wrong VAMI
      mode, causing vCenter/ESXi clock-skew alarms and vSAN "time
      synchronized across hosts and VC" health failures.
    url: "https://knowledge.broadcom.com/external/article/313945"
END-KB-METADATA #}

{% from "vcenter-ntp/map.jinja" import cfg with context %}

vcenter-ntp:
  vcf_vcenter_appliances.ntp_servers:
    - servers: {{ cfg.ntp.servers }}
