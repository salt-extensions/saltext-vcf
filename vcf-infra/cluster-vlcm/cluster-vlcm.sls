{% from "cluster-vlcm/map.jinja" import cfg with context %}

vlcm-depot:
  vcf_esxi_vlcm.depot_configured:
    - depot_type: {{ cfg.depot.type }}
    - location: {{ cfg.depot.location }}

vlcm-image:
  vcf_esxi_vlcm.image_configured:
    - cluster_id: {{ cfg.cluster.id }}
    - image_spec: {{ cfg.image.spec }}
    - require:
      - vcf_esxi_vlcm: vlcm-depot

vlcm-policy:
  vcf_esxi_vlcm.policy_configured:
    - cluster_id: {{ cfg.cluster.id }}
    - policy_spec: {{ cfg.policy.spec }}
    - require:
      - vcf_esxi_vlcm: vlcm-image

vlcm-compliance:
  vcf_esxi_vlcm.compliance_checked:
    - cluster_id: {{ cfg.cluster.id }}
    - require:
      - vcf_esxi_vlcm: vlcm-policy

vlcm-precheck:
  vcf_esxi_vlcm.prechecked:
    - cluster_id: {{ cfg.cluster.id }}
    - require:
      - vcf_esxi_vlcm: vlcm-compliance

vlcm-stage:
  vcf_esxi_vlcm.staged:
    - cluster_id: {{ cfg.cluster.id }}
    - require:
      - vcf_esxi_vlcm: vlcm-precheck

vlcm-remediate:
  vcf_esxi_vlcm.remediated:
    - cluster_id: {{ cfg.cluster.id }}
    - require:
      - vcf_esxi_vlcm: vlcm-stage

vlcm-report:
  vcf_esxi_vlcm.reported:
    - cluster_id: {{ cfg.cluster.id }}
    - require:
      - vcf_esxi_vlcm: vlcm-remediate
