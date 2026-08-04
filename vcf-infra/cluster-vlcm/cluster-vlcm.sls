{% from "cluster-vlcm/map.jinja" import cfg with context %}

vlcm-depot:
  vcf_esxi_vlcm.depot_configured:
    - depot_type: {{ cfg.depot.type }}
    - location: {{ cfg.depot.location }}

{{ cfg.cluster.id }}:
  vcf_esxi_vlcm.image_configured:
    - image_spec: {{ cfg.image.spec }}
    - require:
      - vcf_esxi_vlcm: vlcm-depot
  vcf_esxi_vlcm.policy_configured:
    - policy_spec: {{ cfg.policy.spec }}
    - require:
      - vcf_esxi_vlcm.image_configured: {{ cfg.cluster.id }}
  vcf_esxi_vlcm.compliance_checked:
    - require:
      - vcf_esxi_vlcm.policy_configured: {{ cfg.cluster.id }}
  vcf_esxi_vlcm.prechecked:
    - require:
      - vcf_esxi_vlcm.compliance_checked: {{ cfg.cluster.id }}
  vcf_esxi_vlcm.staged:
    - require:
      - vcf_esxi_vlcm.prechecked: {{ cfg.cluster.id }}
  vcf_esxi_vlcm.remediated:
    - require:
      - vcf_esxi_vlcm.staged: {{ cfg.cluster.id }}
  vcf_esxi_vlcm.reported:
    - require:
      - vcf_esxi_vlcm.remediated: {{ cfg.cluster.id }}
