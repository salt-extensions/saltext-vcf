# Example states and templates

Runnable examples for a handful of `vcf_vim_*` / `vcf_vcenter_*` states, each
self-contained in its own folder with a defaults/override split for its
config values.

## Layout

```
vcf-infra/
├── dvs-pg-vccluster/
│   ├── dvs-pg-vccluster.sls   # the declarative state definition
│   ├── map.jinja              # loads defaults.yaml, applies overrides, exposes `cfg`
│   └── defaults.yaml          # baseline values for this resource
├── guest-vm-vccluster/
│   └── ...same three files...
├── log-forwarder/
├── permission/
├── permission-vccluster/
└── role/
```

Each resource is a standalone folder: the `.sls` file, its `map.jinja`, and
its `defaults.yaml` all live together. `map.jinja` imports `defaults.yaml`,
merges in the resource's specific override values, and exposes the result as
`cfg`:

```jinja
{% import_yaml "<name>/defaults.yaml" as defaults %}
{% set overrides = { ... } %}
{% set cfg = salt['slsutil.merge'](defaults, overrides) %}
```

The `.sls` file consumes it via:

```jinja
{% from "<name>/map.jinja" import cfg with context %}
```

`import_yaml`/`from ... import` resolve against the **saltenv's fileserver
root**, not against the file's own directory. So when you copy `vcf-infra/`
onto a Salt fileserver (or a RaaS "Salt environment"), copy the whole
`vcf-infra/` folder as one unit — each resource folder needs to land as a
top-level directory under the same saltenv root for the imports to resolve.

`salt['slsutil.merge'](defaults, overrides)` deep-merges the two dicts
recursively (`overrides` wins on conflicts), so `defaults.yaml` only needs to
carry values that are safe to reuse across deployments (e.g. port numbers,
protocol, propagate flags) while `map.jinja`'s `overrides` carries the values
that identify this specific deployment (names, hosts, VLAN IDs). One
exception: list values (e.g. `log-forwarder`'s `syslog.servers`) are replaced
wholesale by whichever side defines them — they are not merged item by item.

## Resources

| Resource                | State module                              |
|--------------------------|--------------------------------------------|
| `dvs-pg-vccluster/`       | `vcf_vim_dvs.portgroup_present`            |
| `guest-vm-vccluster/`     | `vcf_vim_vm.present`                       |
| `log-forwarder/`          | `vcf_vcenter_appliance.logging_forwarding` |
| `permission/`             | `vcf_vim_permission.present`               |
| `permission-vccluster/`   | `vcf_vim_permission.present`               |
| `role/`                   | `vcf_vim_role.present`                     |

## Usage

1. Copy the resource's whole folder (e.g. `vcf-infra/dvs-pg-vccluster/`) onto
   your Salt fileserver, keeping its `.sls`/`map.jinja`/`defaults.yaml` as
   siblings.
2. Edit the `overrides` dict in `map.jinja` for the values specific to your
   environment (hostnames, VLAN IDs, roles, etc.); anything left out falls
   back to `defaults.yaml`.
3. Apply the state, e.g.:

   ```bash
   salt '<minion>' state.apply dvs-pg-vccluster.dvs-pg-vccluster saltenv=<your-env> test=true
   ```

   Run with `test=true` first to preview the change, then without it to
   apply for real.
