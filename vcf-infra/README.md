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
its `defaults.yaml` all live together. Every `map.jinja` in this tree now
follows the same Pillar-based pattern — override values are never hardcoded
in `map.jinja`; they're read from Pillar at apply time, keyed by the
resource's own folder name:

```jinja
{% import_yaml "<name>/defaults.yaml" as defaults %}
{% set cfg = salt['pillar.get']('<name>', default=defaults, merge=True) %}
```

The `.sls` file consumes the result the same way everywhere:

```jinja
{% from "<name>/map.jinja" import cfg with context %}
```

`import_yaml`/`from ... import` resolve against the **saltenv's fileserver
root**, not against the file's own directory. So when you copy `vcf-infra/`
onto a Salt fileserver (or a RaaS "Salt environment"), copy the whole
`vcf-infra/` folder as one unit — each resource folder needs to land as a
top-level directory under the same saltenv root for the imports to resolve.

`salt['pillar.get'](key, default, merge=True)` deep-merges Pillar data on top
of `default` recursively (Pillar wins on conflicts), so every formula's
`defaults.yaml` carries a complete, working example config — apply the state
with **no Pillar data at all** and you get exactly the example values below;
supply Pillar under the same top-level key to override just the parts that
differ for your environment. `dvs-pg-vccluster/` is the one exception: its
`defaults.yaml` intentionally omits `dvs.name`/`portgroup.name`/
`portgroup.vlan_id`, so Pillar data is **required** for it to render. One
general merge caveat: list values (e.g. `log-forwarder`'s `syslog.servers`)
are replaced wholesale by whichever side defines them — they are not merged
item by item.

**Nesting convention**: `defaults.yaml` is flattened to top-level keys
(`name:`, `privileges:`, ...) only when a single wrapper key would otherwise
just restate the resource's own name and wrap its *entire* config (see
`role/`, `vc-ad-domain/`, `vc-custom-attribute/`, `vc-dvs-nioc/`,
`vc-dvs-nioc-vccluster/`). Resources with more than one logical section keep
each section nested under its own key instead (see `guest-vm-vccluster/`'s
`vm`/`hardware`/`storage`/`placement`/`network`, or any `cluster-*`/`vc-drs-*`
formula's `cluster:` + its other section) — there's no single wrapper to
eliminate there.

Some `.sls` files (`vccluster-evc`, `vcenter-ntp`) carry a
`{# BEGIN-KB-METADATA ... END-KB-METADATA #}` Jinja comment linking the state
to the real Broadcom KB article that motivated it (id/title/description/url).
This is optional — only add it where a genuine KB reference exists.

## Resources

All resources are Pillar-based (see above); the "Standalone?" column flags
the one exception that requires Pillar data to render at all.

| Resource                   | State module                                  | Standalone? |
|-----------------------------|------------------------------------------------|-------------|
| `cluster-config/`            | `vcf_cluster_config.profile_value`             | Yes |
| `cluster-drs/`                | `vcf_vim_cluster_config.drs`                   | Yes |
| `cluster-ha/`                 | `vcf_vim_cluster_config.ha`                    | Yes |
| `cluster-resource-pool/`      | `vcf_vccluster_resource_pool.shares`           | Yes |
| `dvs-pg-vccluster/`           | `vcf_vim_dvs.portgroup_present`                | **No — Pillar required** |
| `guest-vm-vccluster/`         | `vcf_vim_vm.present`                           | Yes |
| `log-forwarder/`              | `vcf_vcenter_appliance.logging_forwarding`     | Yes |
| `permission/`                 | `vcf_vim_permission.present`                   | Yes |
| `permission-vccluster/`       | `vcf_vim_permission.present`                   | Yes |
| `role/`                       | `vcf_vim_role.present`                         | Yes |
| `vc-ad-domain/`               | `vcf_vcenter_ad_domain.ad_joined`              | Yes |
| `vc-advanced-option/`         | `vcf_vcenter_advanced_option.advanced_option`  | Yes |
| `vc-content-library/`         | `vcf_vcenter_content_library.present`          | Yes |
| `vc-custom-attribute/`        | `vcf_vcenter_custom_attribute.present`         | Yes |
| `vc-dns/`                     | `vcf_vcenter_appliance.dns_servers`            | Yes |
| `vc-drs-group-absent/`        | `vcf_vim_drs_rule.group_absent`                | Yes |
| `vc-drs-host-group/`          | `vcf_vim_drs_rule.host_group`                  | Yes |
| `vc-drs-vm-group/`            | `vcf_vim_drs_rule.vm_group`                    | Yes |
| `vc-drs-vm-host/`             | `vcf_vim_drs_rule.vm_host`                     | Yes |
| `vc-dvs-nioc/`                | `vcf_vcenter_dvs_nioc.nioc_enabled`            | Yes |
| `vc-dvs-nioc-vccluster/`      | `vcf_vcenter_dvs_nioc_vccluster.nioc_enabled`  | Yes |
| `vc-dvs-portgroup/`           | `vcf_vim_dvs.portgroup_present` / `portgroup_absent` | Yes |
| `vc-ntp/`                     | `vcf_vcenter_appliances.ntp_servers`           | Yes |
| `vc-shell/`                   | `vcf_vcenter_shell.shell_access`               | Yes |
| `vccluster-evc/`              | `vcf_vim_cluster_evc.mode`                     | Yes |
| `vcenter-ntp/`                | `vcf_vcenter_appliances.ntp_servers`           | Yes |

Note: `vc-ntp/` and `vcenter-ntp/` both drive the same state module
(`vcf_vcenter_appliances.ntp_servers`) — `vcenter-ntp/` additionally documents
its motivating KB article. Consider consolidating on one of the two.

## Usage

1. Copy the resource's whole folder (e.g. `vcf-infra/cluster-config/`) onto
   your Salt fileserver, keeping its `.sls`/`map.jinja`/`defaults.yaml` as
   siblings.
2. To use it as-is (any resource marked "Yes" above), apply it with no
   Pillar data — you get the example values baked into `defaults.yaml`. To
   point it at your own environment, assign Pillar data under a top-level
   key matching the resource's folder name, e.g. for `cluster-config/`:

   ```yaml
   cluster-config:
     cluster:
       name: domain-c9
   ```

   Anything left out of Pillar falls back to `defaults.yaml`. For
   `dvs-pg-vccluster/` (the one resource marked "No" above), Pillar data for
   `dvs.name`/`portgroup.name`/`portgroup.vlan_id` is required — it has no
   standalone default.
3. Apply the state, e.g.:

   ```bash
   salt '<minion>' state.apply cluster-config.cluster-config saltenv=<your-env> pillar='{"cluster-config": {"cluster": {"name": "domain-c9"}}}' test=true
   ```

   (or rely on Pillar already assigned to the target via `pillar_roots`/an
   external pillar source, in which case the inline `pillar=` argument above
   isn't needed). Run with `test=true` first to preview the change, then
   without it to apply for real.
