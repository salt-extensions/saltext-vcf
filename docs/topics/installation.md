# Installation

Install into the same Python environment Salt uses.

:::{tab} salt-pip (Onedir)
```bash
salt-pip install saltext-vmware
```
:::

:::{tab} pip
```bash
pip install saltext-vmware
```
:::

:::{tab} Salt state
```yaml
Install saltext-vmware:
  pip.installed:
    - name: saltext-vmware
```
:::

Saltexts are not distributed via the fileserver. Install on every node
that needs the modules.

## Extras

Base install pulls `pyvmomi` (SOAP/VMODL) and `pywbem` (CIM/WBEM).

| Extra | Adds |
|---|---|
| `[vcenter]` | `vmware-vcenter` SDK |
| `[sddc]` | `vmware-vcf` SDK |
| `[vks]` | `saltext-kubernetes` + `kubernetes` for the VKS kubeconfig bridge |

```bash
pip install 'saltext-vmware[vks]'
```

## Verify

```bash
salt-call --local sys.list_modules | grep vmware_
salt-call --local sys.list_states  | grep vmware_
```

Expect ~80 modules and ~27 states. If empty, the install landed in a
different Python than Salt's:

```bash
salt-call --local config.get pip_target
salt-call --local sys.doc vmware_vcenter_cluster
```

## Salt version

Targets Salt 3006+. The `saltext.vmware.resources` subpackage requires
`salt.utils.resources`; on builds without it, `__virtual__` returns
`False` and the resources framework integration is unavailable. The
flat-pillar path still works.

## Next

* [Configuration](configuration.md)
* [Reference](../ref/modules/index.rst)
