# saltext.vcf

Salt extension for VMware Cloud Foundation 9.x. Targets the full VCF
stack: vCenter, NSX, SDDC Manager, VCF Operations, VKS (Supervisor),
VMSP (mediated), vSAN, and standalone ESXi.

## Coverage

- **vCenter** — REST `/api/` for clusters, hosts, VMs, datacenters,
  datastores, networks, storage policies, content libraries, folders,
  resource pools, tags, custom attributes, appliance services, KMS
  providers; pyVmomi/SOAP for alarms, perf, extensions, VM snapshots.
- **vSphere 9 Cluster Configuration Profile** — desired-state profile
  API for vCenter-managed clusters (replaces direct ESXi REST).
- **ESXi Lifecycle (vLCM patching)** — depot config/sync, desired-image
  drafts, cluster apply policy, and compliance/precheck/stage/remediate
  against vCenter's ESX Lifecycle Manager REST API.
- **VC Patch** — VCSA self-update via the VAMI appliance-update API:
  repository config, staging with idempotency/stage-timeout recovery,
  precheck, and install.
- **NSX** — Policy API (segments, tier-0/tier-1, groups, security
  policies, firewall rules, services, context profiles, NAT, IP
  blocks/pools, DHCP, edge clusters) and Management API (node,
  cluster status, transport zones/nodes, compute collections, RBAC).
- **SDDC Manager** — hosts, clusters, workload domains, vCenters,
  bundles, network pools, releases, upgrades, certificates,
  credentials, VMSP service health via `/v1/vcf-services`.
- **VCF Operations** — resources, adapters, alert/symptom definitions,
  active alerts, policies, notifications, recommendations, RBAC
  (sources/roles/users/groups/privileges), collectors, credentials,
  super metrics, resource groups, reports, maintenance schedules,
  tasks, solutions, node status.
- **VKS** — Supervisor enablement, services catalog, namespaces, VM
  classes, software lifecycle, compatibility probes, kubeconfig fetch
  bridge to [saltext-kubernetes].
- **vSAN** — cluster config, disk groups, fault domains, health (SOAP
  at `/vsanHealth`).
- **Salt Resources framework** — `vcenter`, `sddc`, `nsx`, `vcfops`,
  `esxi`, `vcf_vm` resource types for fleet-style management with
  grain-based targeting.

~80 execution modules, 27 state modules, 82 REST/SOAP clients across
six VCF components.

## Quickstart

Base install ships the core Salt loader wiring and the REST client
plumbing only. Every runtime dependency (pyvmomi, pywbem, the VMware
SDKs, kubernetes) is opt-in via pip extras — pick the components you
plan to use, or install everything with `[all]`:

```bash
pip install saltext.vcf            # base only; most modules will not load
pip install 'saltext.vcf[all]'     # equivalent to the pre-split default
pip install 'saltext.vcf[vcenter,nsx]'
```

See [Installing sub-components](#installing-sub-components) below for
the full list of extras.

Configure pillar:

```yaml
saltext.vcf:
  vcenter:
    host: mgmt-vc.example.com
    username: administrator@vsphere.local
    password: secret
    verify_ssl: false
  sddc_manager:
    host: sddc-manager.example.com
    username: administrator@vsphere.local
    password: secret
    verify_ssl: false
  nsx:
    host: mgmt-nsx.example.com
    username: admin
    password: secret
    verify_ssl: false
  vcf_ops:
    host: ops.example.com
    username: admin
    password: secret
    verify_ssl: false
```

Run from any minion with the extension installed:

```bash
salt-call vcf_vcenter_cluster.list_
salt-call vcf_sddc_domain.list_
salt-call vcf_nsx_segment.list_
salt-call vcf_vcfops_deployment.healthy
salt-call vcf_vcf_services.status_map
```

## Installing sub-components

`saltext.vcf` is split into per-component extras. The base install is
minimal on purpose — modules whose deps are missing return
`__virtual__ = False` and are silently skipped by the Salt loader.
Pick the extras that match the VCF surface area you actually manage:

| Extra | Adds | Enables |
|---|---|---|
| `[esxi]` | `pyvmomi`, `pywbem` | Standalone ESXi (`vcf_esxi_*`), CIM hardware health, vSAN SOAP helpers |
| `[vcenter]` | `pyvmomi`, `vmware-vcenter` SDK | vCenter REST + SOAP (`vcf_vcenter_*`, `vim_*` clients, alarms, perf, snapshots) |
| `[nsx]` | — (uses `requests` only) | NSX Policy + Management API (`vcf_nsx_*`) |
| `[sddc]` | `vmware-vcf` SDK | SDDC Manager (`vcf_sddc_*`) |
| `[vcfops]` | — (uses `requests` only) | VCF Operations (`vcf_vcfops_*`) |
| `[vcfa]` | — (uses `requests` only) | VCF Automation (`vcf_vcfa_*`) |
| `[installer]` | `pyvmomi` | VCF Installer OVA deploy (`vcf_installer_*`) |
| `[vks]` | `saltext.kubernetes`, `kubernetes` | VKS Supervisor kubeconfig bridge |
| `[all]` | Every runtime extra above | Matches the pre-split default install |

```bash
pip install 'saltext.vcf[vcenter,nsx,sddc]'
pip install 'saltext.vcf[all]'   # everything
```

## Documentation

Full docs at <https://salt-extensions.github.io/saltext-vcf/>.

Local build:

```bash
pip install -e '.[docs]'
make -C docs html
xdg-open docs/_build/html/index.html
```

Topic guides under `docs/topics/`:
- [Installation](docs/topics/installation.md)
- [Configuration](docs/topics/configuration.md)
- [Resources Framework](docs/topics/resources-framework.md)
- [VKS / Supervisor bridge](docs/topics/vks-bridge.md)
- [vSAN over SOAP](docs/topics/vsan-soap.md)
- [VMSP mediated access](docs/topics/vmsp-mediated.md)

Examples per component live under `docs/examples/`.

## Development

```bash
pip install -e '.[dev,tests,lint]'
pre-commit install
pytest tests/ -q
```

Live integration tests run against a real VCF lab and live in a separate
integration repository; they're not part of the unit test suite here.

## License

Apache 2.0. See [LICENSE](LICENSE).

[saltext-kubernetes]: https://github.com/salt-extensions/saltext-kubernetes
