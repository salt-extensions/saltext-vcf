{#
  vcenter_storage_policy_vccluster (Ansible item #75) authors a named SPBM
  storage policy (capability/tag rulesets) -- the same operation
  PowerCLI's New-/Set-SpbmStoragePolicy wraps. It does not itself assign
  the policy as a cluster/datastore default; that's a separate PBM call
  this example doesn't cover.
#}
{% from "vc-storage-policy/map.jinja" import cfg with context %}

{{ cfg.policy.name }}:
  vcf_vcenter_storage_policy.present:
    - description: {{ cfg.policy.description }}
    - constraints: {{ cfg.policy.constraints }}
