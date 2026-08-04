{% from "cluster-vsan/map.jinja" import cfg with context %}

{{ cfg.cluster.id }}:
  vcf_vsan_cluster.configured:
    - enabled: {{ cfg.vsan.enabled }}
    - dedup_compression_enabled: {{ cfg.vsan.dedup_compression_enabled }}
    - encryption_enabled: {{ cfg.vsan.encryption_enabled }}
    - auto_claim_storage: {{ cfg.vsan.auto_claim_storage }}
