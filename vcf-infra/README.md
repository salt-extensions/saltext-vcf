# Example states and templates

Runnable examples for a handful of `vcf_vim_*` / `vcf_vcenter_*` states,
paired with the config values they consume.

## Layout

```
vcf-infra/
├── states/      # SLS files - the declarative state definitions
└── templates/   # YAML config consumed by the matching state via import_yaml
```

`states/` and `templates/` are siblings by design. Each SLS file pulls its
config with:

```jinja
{% import_yaml "templates/<name>-template.yaml" as cfg %}
```

`import_yaml` resolves that path against the **saltenv's fileserver root**,
not against the SLS file's own directory. So when you copy this `vcf-infra/`
folder onto a Salt fileserver (or a RaaS "Salt environment"), `states/` and
`templates/` need to land as top-level siblings under the same saltenv root
for the import to resolve — copy the whole `vcf-infra/` folder as one unit,
not just the `states/` half.

## Naming convention

Each state file has a matching template file with a `-template` suffix:

| State                       | Template                                |
|------------------------------|------------------------------------------|
| `dvs-pg-vccluster.sls`        | `dvs-pg-vccluster-template.yaml`         |
| `guest-vm-vccluster.sls`      | `guest-vm-vccluster-template.yaml`       |
| `log-forwarder.sls`           | `log-forwarder-template.yaml`            |
| `permission.sls`              | `permission-template.yaml`               |
| `permission-vccluster.sls`    | `permission-vccluster-template.yaml`     |
| `role.sls`                    | `role-template.yaml`                     |

## Usage

1. Copy `vcf-infra/states/*` and `vcf-infra/templates/*` onto your Salt
   fileserver, preserving the `states/` + `templates/` sibling layout.
2. Edit the template YAML for the resource you want to manage (hostnames,
   VLAN IDs, roles, etc. are specific to your environment).
3. Apply the state, e.g.:

   ```bash
   salt '<minion>' state.apply states.role saltenv=<your-env> test=true
   ```

   Run with `test=true` first to preview the change, then without it to
   apply for real.
