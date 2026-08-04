{% from "cluster-resource-pool/map.jinja" import cfg with context %}

vcf_cluster_resource_pool:
  vcf_vccluster_resource_pool.shares:
    - name: {{ cfg.cluster.name }}
    - cpu: {{ cfg.shares.cpu }}
    - memory: {{ cfg.shares.memory }}
