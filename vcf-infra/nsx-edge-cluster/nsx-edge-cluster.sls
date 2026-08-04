{% from "nsx-edge-cluster/map.jinja" import cfg with context %}

nsx-edge-cluster:
  module.run:
    - name: vcf_nsx_edge_cluster.create
    - body: {{ cfg.edge_cluster.body }}
