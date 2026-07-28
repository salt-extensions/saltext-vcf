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

The base install ships the Salt loader wiring and REST plumbing only.
Every third-party runtime dep (pyvmomi, pywbem, the VMware SDKs,
kubernetes) is opt-in via a pip extra. Modules whose deps are missing
return `__virtual__ = False` and are silently skipped by the loader —
install just the components you use, or use `[all]` for the pre-split
default.

| Extra | Adds | Enables |
|---|---|---|
| `[esxi]` | `pyvmomi`, `pywbem` | Standalone ESXi (`vcf_esxi_*`), CIM hardware health, vSAN SOAP helpers |
| `[vcenter]` | `pyvmomi`, `vmware-vcenter` SDK | vCenter REST + SOAP (`vcf_vcenter_*`, `vim_*` clients) |
| `[nsx]` | — (uses `requests` only) | NSX Policy + Management API (`vcf_nsx_*`) |
| `[sddc]` | `vmware-vcf` SDK, `paramiko` | SDDC Manager (`vcf_sddc_*`), including appliance-local SSH controls |
| `[vcfops]` | — (uses `requests` only) | VCF Operations (`vcf_vcfops_*`) |
| `[vcfa]` | — (uses `requests` only) | VCF Automation (`vcf_vcfa_*`) |
| `[installer]` | `pyvmomi` | VCF Installer OVA deploy (`vcf_installer_*`) |
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
