# Installation

Install into the same Python environment Salt uses.

:::{tab} salt-pip (Onedir)
```bash
salt-pip install saltext-vcf
```
:::

:::{tab} pip
```bash
pip install saltext-vcf
```
:::

:::{tab} Salt state
```yaml
Install saltext-vcf:
  pip.installed:
    - name: saltext-vcf
```
:::

Saltexts are not distributed via the fileserver. Install on every node
that needs the modules.

## Sub-component extras

The base install ships the Salt loader wiring, REST plumbing, and
pyvmomi for the whole SOAP surface (vCenter/ESXi vim clients). The
remaining third-party runtime deps (pywbem, the VMware SDKs,
kubernetes) are opt-in via a pip extra. Modules whose remaining deps
are missing return `__virtual__ = False` and are silently skipped by
the loader — install just the components you use, or use `[all]` for
every runtime dependency.

| Extra | Adds | Enables |
|---|---|---|
| `[esxi]` | `pywbem` | CIM hardware health on standalone ESXi (`vcf_esxi_*` CIM checks) |
| `[vcenter]` | `vmware-vcenter` SDK | vCenter SDK-typed flows (`vcf_vcenter_*` SDK paths, alarms, perf, snapshots) |
| `[nsx]` | — (uses `requests` only) | NSX Policy + Management API (`vcf_nsx_*`) |
| `[sddc]` | `vmware-vcf` SDK, `paramiko` | SDDC Manager (`vcf_sddc_*`), including appliance-local SSH controls |
| `[vcfops]` | — (uses `requests` only) | VCF Operations (`vcf_vcfops_*`) |
| `[vcfa]` | — (uses `requests` only) | VCF Automation (`vcf_vcfa_*`) |
| `[installer]` | — (pyvmomi is base now) | VCF Installer OVA deploy (`vcf_installer_*`) |
| `[vks]` | `saltext.kubernetes`, `kubernetes` | VKS Supervisor kubeconfig bridge |
| `[all]` | Every runtime extra above | Matches the pre-split default install |

```bash
pip install 'saltext-vcf[vcenter,nsx]'
pip install 'saltext-vcf[all]'
```

## Verify

```bash
salt-call --local sys.list_modules | grep vcf_
salt-call --local sys.list_states  | grep vcf_
```

Expect ~80 modules and ~27 states. If empty, the install landed in a
different Python than Salt's:

```bash
salt-call --local config.get pip_target
salt-call --local sys.doc vcf_vcenter_cluster
```

## Salt version

Targets Salt 3006+. The `saltext.vcf.resources` subpackage requires
`salt.utils.resources`; on builds without it, `__virtual__` returns
`False` and the resources framework integration is unavailable. The
flat-pillar path still works.

## Next

* [Configuration](configuration.md)
* [Reference](../ref/modules/index.rst)
