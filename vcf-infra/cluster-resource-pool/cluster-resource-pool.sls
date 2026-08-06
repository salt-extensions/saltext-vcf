{% from "cluster-resource-pool/map.jinja" import cfg with context %}

{{ cfg.pool.name }}:
  vcf_vccluster_resource_pool.present:
    - cluster: {{ cfg.cluster.name }}
    - cpu: {{ cfg.shares.cpu }}
    - memory: {{ cfg.shares.memory }}
