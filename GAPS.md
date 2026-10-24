# Known gaps in saltext-vcf

Comparison reference: `saltext-vcf-automation` (internal Broadcom day-0
VCF deployer in `vcf/mops`, branch
`feature/VCOPS-99999-vcf-salt-automation`). The end-to-end VCF deploy
test in `saltext-vcf-integration/live_tests/vcf_installer/test_e2e_full_deploy.py`
already exercises the saltext-vcf modules needed for VCF bringup. The
items below are *operating*-time gaps surfaced by the comparison —
they don't block the deploy test but they limit how much of the
`saltext-vcf-automation` reference functionality is replicated.

## NSX transport zone CRUD

CLOSED — `clients/nsx_transport_zone.py` exposes `list_`/`get`/`create`/
`update`/`delete`, `modules/vcf_nsx_transport_zone.py` mirrors them, and
`states/vcf_nsx_transport_zone.py` provides `present`/`absent`.

## SDDC workload domain CRUD via exec module

CLOSED — `modules/vcf_sddc_domain.py` and
`states/vcf_sddc_domain.py` expose the create/update/delete/validate
surface that already existed in `clients/sddc_domain.py`.

## ESXi config aggregator

`saltext-vcf-automation`'s `vcf_esxi.get_config(fqdn)` /
`set_config(fqdn, config)` is a single aggregator over ESXi-host config.
saltext-vcf splits the same surface across six modules —
`vcf_esxi_advanced`, `vcf_esxi_firewall`, `vcf_esxi_host`,
`vcf_esxi_ntp`, `vcf_esxi_service`, `vcf_esxi_syslog` — which is more
faithful to the underlying REST APIs but more friction for callers
who want one round trip per host.

No new client code is needed; an aggregator module/state would
orchestrate the existing per-area clients.

## State modules for already-supported exec ops

CLOSED — `states/vcf_sddc_domain.py`, `states/vcf_sddc_host.py` and
`states/vcf_nsx_transport_zone.py` all exist.

## OVF deploy: pyVmomi vs ovftool

`clients/ovf_deploy.deploy_ova` is a pure pyVmomi implementation
(`OvfManager.CreateImportSpec` + `ResourcePool.ImportVApp` +
`HttpNfcLease` streaming PUT) and `clients/ovftool_deploy.deploy_ova`
provides an ovftool-subprocess backend for the same operation
(backend selectable at the client level; the product-specific exec
modules route through the pyVmomi path). `clients/vim_ovf.py` exports
OVFs via the same lease mechanism.

Not blocking anything today.

## vSphere parity with saltext-vmware

DONE — the missing and partial vSphere/pyVmomi surface from the
`saltext-vmware` extension has been ported into saltext-vcf's
conventions. The function-level ledger (what was ported, what was
already covered, and known deviations) lives in
`docs/topics/vsphere-parity.md`.
