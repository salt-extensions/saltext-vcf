# Example states and templates

Runnable examples for a handful of `vcf_vim_*` / `vcf_vcenter_*` states, each
self-contained in its own folder with a defaults/override split for its
config values.

## Layout

```
vcf-infra/
├── cluster-config/
│   ├── cluster-config.sls    # the declarative state definition
│   ├── map.jinja              # loads defaults.yaml, applies overrides, exposes `cfg`
│   └── defaults.yaml          # baseline values for this resource
├── cluster-drs/
├── cluster-ha/
├── cluster-resource-pool/
├── dvs-pg-vccluster/
├── guest-vm-vccluster/
├── log-forwarder/
├── permission/
├── permission-vccluster/
├── role/
├── vc-ad-domain/
├── vc-advanced-option/
├── vc-content-library/
├── vc-custom-attribute/
├── vc-dns/
├── vc-drs-group-absent/
├── vc-drs-host-group/
├── vc-drs-vm-group/
├── vc-drs-vm-host/
├── vc-dvs-nioc/
├── vc-dvs-nioc-vccluster/
├── vc-dvs-portgroup/
├── vc-ntp/
├── vc-shell/
├── vccluster-evc/
└── vcenter-ntp/
    └── ...same three files as cluster-config/...
```

Each resource is a standalone folder: the `.sls` file, its `map.jinja`, and
its `defaults.yaml` all live together. `map.jinja` imports `defaults.yaml`
and exposes the merged result as `cfg`. There are two variants of `map.jinja`
in use here:

**Pillar-based overrides** (`dvs-pg-vccluster/` and everything else except
the handful noted below) — no override values live in the repo at all;
they're read from Pillar at apply time, keyed by the resource's own name:

```jinja
{% import_yaml "<name>/defaults.yaml" as defaults %}
{% set cfg = salt['pillar.get']('<name>', default=defaults, merge=True) %}
```

**Inline overrides** (`guest-vm-vccluster/`, `log-forwarder/`, `permission/`,
`permission-vccluster/`, `role/`, `vccluster-evc/`, `vcenter-ntp/` — not yet
migrated to the pillar-based pattern) — override values are hardcoded in
`map.jinja` itself:

```jinja
{% import_yaml "<name>/defaults.yaml" as defaults %}
{% set overrides = { ... } %}
{% set cfg = salt['slsutil.merge'](defaults, overrides) %}
```

Either way, the `.sls` file consumes `cfg` the same way:

```jinja
{% from "<name>/map.jinja" import cfg with context %}
```

`import_yaml`/`from ... import` resolve against the **saltenv's fileserver
root**, not against the file's own directory. So when you copy `vcf-infra/`
onto a Salt fileserver (or a RaaS "Salt environment"), copy the whole
`vcf-infra/` folder as one unit — each resource folder needs to land as a
top-level directory under the same saltenv root for the imports to resolve.

Both `salt['pillar.get'](key, default, merge=True)` and
`salt['slsutil.merge'](defaults, overrides)` deep-merge recursively (the
Pillar/override side wins on conflicts), so `defaults.yaml` only needs to
carry values that are safe to reuse across deployments (e.g. port numbers,
protocol, propagate flags) while Pillar/`overrides` carries the values that
identify this specific deployment (names, hosts, VLAN IDs, moids). One
exception: list values (e.g. `log-forwarder`'s `syslog.servers`) are replaced
wholesale by whichever side defines them — they are not merged item by item.
Some resources (e.g. `vc-advanced-option`, `vc-dns`, `vc-ntp`) have nothing
truly deployment-specific to override, so their `defaults.yaml` carries
everything and there's no Pillar data required to render a working example —
but for pillar-based resources whose `defaults.yaml` is empty (e.g.
`dvs-pg-vccluster`, `vc-content-library`, the `vc-drs-*` group formulas),
Pillar data is **required** — the `.sls` will fail to render without it.

Some `.sls` files (`vccluster-evc`, `vcenter-ntp`) carry a
`{# BEGIN-KB-METADATA ... END-KB-METADATA #}` Jinja comment linking the state
to the real Broadcom KB article that motivated it (id/title/description/url).
This is optional — only add it where a genuine KB reference exists.

## Resources

| Resource                   | State module                                  | Overrides via |
|-----------------------------|------------------------------------------------|----------------|
| `cluster-config/`            | `vcf_cluster_config.profile_value`             | Pillar |
| `cluster-drs/`                | `vcf_vim_cluster_config.drs`                   | Pillar |
| `cluster-ha/`                 | `vcf_vim_cluster_config.ha`                    | Pillar |
| `cluster-resource-pool/`      | `vcf_vccluster_resource_pool.shares`           | Pillar |
| `dvs-pg-vccluster/`           | `vcf_vim_dvs.portgroup_present`                | Pillar |
| `guest-vm-vccluster/`         | `vcf_vim_vm.present`                           | `map.jinja` |
| `log-forwarder/`              | `vcf_vcenter_appliance.logging_forwarding`     | `map.jinja` |
| `permission/`                 | `vcf_vim_permission.present`                   | `map.jinja` |
| `permission-vccluster/`       | `vcf_vim_permission.present`                   | `map.jinja` |
| `role/`                       | `vcf_vim_role.present`                         | `map.jinja` |
| `vc-ad-domain/`               | `vcf_vcenter_ad_domain.ad_joined`              | Pillar |
| `vc-advanced-option/`         | `vcf_vcenter_advanced_option.advanced_option`  | Pillar |
| `vc-content-library/`         | `vcf_vcenter_content_library.present`          | Pillar |
| `vc-custom-attribute/`        | `vcf_vcenter_custom_attribute.present`         | Pillar |
| `vc-dns/`                     | `vcf_vcenter_appliance.dns_servers`            | Pillar |
| `vc-drs-group-absent/`        | `vcf_vim_drs_rule.group_absent`                | Pillar |
| `vc-drs-host-group/`          | `vcf_vim_drs_rule.host_group`                  | Pillar |
| `vc-drs-vm-group/`            | `vcf_vim_drs_rule.vm_group`                    | Pillar |
| `vc-drs-vm-host/`             | `vcf_vim_drs_rule.vm_host`                     | Pillar |
| `vc-dvs-nioc/`                | `vcf_vcenter_dvs_nioc.nioc_enabled`            | Pillar |
| `vc-dvs-nioc-vccluster/`      | `vcf_vcenter_dvs_nioc_vccluster.nioc_enabled`  | Pillar |
| `vc-dvs-portgroup/`           | `vcf_vim_dvs.portgroup_present` / `portgroup_absent` | Pillar |
| `vc-ntp/`                     | `vcf_vcenter_appliances.ntp_servers`           | Pillar |
| `vc-shell/`                   | `vcf_vcenter_shell.shell_access`               | Pillar |
| `vccluster-evc/`              | `vcf_vim_cluster_evc.mode`                     | `map.jinja` |
| `vcenter-ntp/`                | `vcf_vcenter_appliances.ntp_servers`           | `map.jinja` |

Note: `vc-ntp/` and `vcenter-ntp/` both drive the same state module
(`vcf_vcenter_appliances.ntp_servers`) — `vcenter-ntp/` additionally documents
its motivating KB article. Consider consolidating on one of the two.

## Usage

1. Copy the resource's whole folder (e.g. `vcf-infra/cluster-config/`) onto
   your Salt fileserver, keeping its `.sls`/`map.jinja`/`defaults.yaml` as
   siblings.
2. Supply the deployment-specific values:
   - **Pillar-based resources** (see the table above): assign Pillar data
     under a top-level key matching the resource's folder name, e.g. for
     `cluster-config/`:

     ```yaml
     cluster-config:
       cluster:
         name: domain-c9
     ```

     Anything left out of Pillar falls back to `defaults.yaml`; for
     resources with an empty `defaults.yaml` (e.g. `dvs-pg-vccluster/`,
     `vc-content-library/`, the `vc-drs-*` formulas), Pillar data is
     required.
   - **`map.jinja`-based resources** (see the table above): edit the
     `overrides` dict directly in that resource's `map.jinja`.
3. Apply the state, e.g.:

   ```bash
   salt '<minion>' state.apply cluster-config.cluster-config saltenv=<your-env> pillar='{"cluster-config": {"cluster": {"name": "domain-c9"}}}' test=true
   ```

   (or rely on Pillar already assigned to the target via `pillar_roots`/an
   external pillar source, in which case the inline `pillar=` argument above
   isn't needed). Run with `test=true` first to preview the change, then
   without it to apply for real.
