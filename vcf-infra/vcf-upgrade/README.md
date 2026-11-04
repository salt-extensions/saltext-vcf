# VCF upgrade state

Expose `vcf-infra/` as a Salt file root, as for the existing `vc-patch` formula.
Configure connections under `saltext.vcf:sddc_manager` and upgrade inputs under
`saltext.vcf:vcf_upgrade`. An absent target fails before any submission.

```bash
salt-call state.apply vcf-upgrade.vcf-upgrade test=true
salt-call state.apply vcf-upgrade.vcf-upgrade
```

Without `sequence`, the state upgrades `component_type` (default `SDDC_MANAGER`).
With an explicit `sequence`, it runs the configured components in order. Rerun
with the same inputs and checkpoint to resume. See
[configuration and recovery](../../docs/topics/vcf-upgrade.md) before deployment.
