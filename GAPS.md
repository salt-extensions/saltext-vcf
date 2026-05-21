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

`src/saltext/vcf/clients/nsx_transport_zone.py` and
`src/saltext/vcf/modules/vcf_nsx_transport_zone.py` only expose `list_`
and `get`. Reference parity needs `create`, `update`, `delete`, plus a
state module `states/vcf_nsx_transport_zone.py` with a
`transport_zone_present(name, zone_type)` function.

NSX transport zones are normally created by the VCF Installer as part
of bringup (which is why the deploy test doesn't need this), but
day-2 zone management — adding an overlay TZ for a new workload domain,
removing a deprecated VLAN TZ — has no Salt-driven path today.

## SDDC workload domain CRUD via exec module

`src/saltext/vcf/clients/sddc_domain.py` already implements `create`,
`update`, `delete`, `mark_for_deletion`, and `validate` against
`/v1/domains`. The exec module
`src/saltext/vcf/modules/vcf_sddc_domain.py` only surfaces `list_` and
`get`, so the create/update/delete client functions aren't reachable
from a Salt state.

This is the cheapest gap to close: just add module wrappers that call
the existing client functions, plus a `states/vcf_sddc_domain.py` with
`present(name, spec)` / `absent(name)`.

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

The following exec modules ship with the operations but have no
state-module counterpart, so they can't be driven from a `state.apply`:

- `states/vcf_sddc_domain.py` — wraps the CRUD gap above.
- `states/vcf_sddc_host.py` — `commissioned(name, host_specs)` /
  `decommissioned(name)` against
  `modules/vcf_sddc_host.commission/decommission`. The exec module
  works today; only the declarative wrapper is missing.
- `states/vcf_nsx_transport_zone.py` — depends on the NSX CRUD gap.

## OVF deploy: pyVmomi vs ovftool

`clients/ovf_deploy.deploy_ova` is a pure pyVmomi implementation
(`OvfManager.CreateImportSpec` + `ResourcePool.ImportVApp` +
`HttpNfcLease` streaming PUT). `clients/vim_ovf.py` exports OVFs via
the same lease mechanism — there's no ovftool subprocess dependency
anywhere in saltext-vcf.

`saltext-vcf-automation`'s OVA deploy uses `ovftool` subprocess. If
operators prefer ovftool's deeper handling of OVF properties /
networks for non-VCF-Installer OVAs, an `ovftool`-driven path could be
added as a separate client (or as an alternative backend to
`deploy_ova(..., backend="ovftool")`). Not blocking anything today.
