{% import_yaml "templates/vc-cluster-resource-pool-template.yaml" as cfg %}

vc-cluster-resource-pool:
  vcf_vccluster_resource_pool.shares:
    - name: {{ cfg.cluster.name }}:
    - cpu: {{ cfg.shares.cpu }}
    - memory: {{ cfg.shares.memory }}
