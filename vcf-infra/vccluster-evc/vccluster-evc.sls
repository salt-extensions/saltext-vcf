{# BEGIN-KB-METADATA
kb:
  - id: "339901"
    title: "Adding an ESXi host with a CPU similar to the EVC baseline to a cluster"
    description: >-
      Adding a host into an EVC-enabled cluster without following the
      power-off/maintenance-mode sequence causes "host CPU lacks features
      required by that mode" errors and host disconnects.
    url: "https://knowledge.broadcom.com/external/article/339901"
END-KB-METADATA #}

{% from "vccluster-evc/map.jinja" import cfg with context %}

vccluster-evc:
  vcf_vim_cluster_evc.mode:
    - cluster: {{ cfg.cluster }}
    - evc_mode_key: {{ cfg.evc.mode }}
