{% from "cluster-vsan/map.jinja" import cfg with context %}

{{ cfg.cluster.id }}:
  vcf_vsan_cluster.configured:
    - enabled: {{ cfg.vsan.enabled }}
    - dedup_compression_enabled: {{ cfg.vsan.dedup_compression_enabled }}
    - encryption_enabled: {{ cfg.vsan.encryption_enabled }}
    - auto_claim_storage: {{ cfg.vsan.auto_claim_storage }}

{# Requires cfg.datastore.storage_policy to already exist as a named policy
   -- e.g. via vc-storage-policy/, applied ahead of this in the same run. #}
{{ cfg.datastore.name }}-default-policy:
  vcf_vcenter_storage_policy.default_policy:
    - datastore: {{ cfg.datastore.name }}
    - policy: {{ cfg.datastore.storage_policy }}
