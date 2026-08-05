# Example states and templates

Runnable examples for `vcf_vim_*` / `vcf_vcenter_*` / `vcf_nsx_*` / `vcf_sddc_*`
/ `vcf_esxi_*` states (55 resources), each self-contained in its own folder
with a defaults/override split for its config values.

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
├── cluster-vlcm/
├── cluster-vsan/
├── dvs-pg-vccluster/
├── esxi-buffer-size/
├── esxi-config/
├── esxi-kernel-module/
├── esxi-shell-access/
├── guest-vm-vccluster/
├── installer-depot/
├── log-forwarder/
├── nsx-edge-cluster/
├── nsxt-dhcp/
├── nsxt-firewall-policy/
├── nsxt-role-binding/
├── nsxt-segment/
├── nsxt-tier0/
├── nsxt-tier1/
├── permission/
├── permission-vccluster/
├── role/
├── sddc-bringup/
├── sddc-bundles/
├── sddc-domain/
├── sddc-host/
├── sddc-manager-feature/
├── sddc-manager-local-accounts/
├── sddc-personality/
├── sddc-removal/
├── sddc-users/
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
├── vc-patch/
├── vc-shell/
├── vccluster-evc/
├── vccluster-vm-vm-affinity/
├── vcenter-identity-source/
├── vcenter-nkp/
├── vcenter-ntp/
├── vcenter-service/
└── vcenter-sso-group/
    └── ...same three files as cluster-config/...
```

Each resource is a standalone folder: the `.sls` file, its `map.jinja`, and
its `defaults.yaml` all live together. Every `map.jinja` in this tree follows
the same Pillar-based pattern — override values are never hardcoded in
`map.jinja`; they're read from Pillar at apply time, keyed by the resource's
own folder name:

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
differ for your environment. One general merge caveat: list values (e.g.
`log-forwarder`'s `syslog.servers`) are replaced wholesale by whichever side
defines them — they are not merged item by item. See **Known issues** below
for the two resources whose `defaults.yaml` isn't fully self-contained.

**Nesting convention**: `defaults.yaml` is flattened to top-level keys
(`name:`, `privileges:`, ...) only when a single wrapper key would otherwise
just restate the resource's own name and wrap its *entire* config (see
`role/`, `vc-ad-domain/`, `vc-custom-attribute/`, `vc-dvs-nioc/`,
`vc-dvs-nioc-vccluster/`). Resources with more than one logical section keep
each section nested under its own key instead (see `guest-vm-vccluster/`'s
`vm`/`hardware`/`storage`/`placement`/`network`, `esxi-config/`'s six
independent sub-sections, or any `cluster-*`/`vc-drs-*`/`sddc-*` formula's
top-level identity key plus its other section) — there's no single wrapper to
eliminate there.

Some `.sls` files (`vccluster-evc`, `vcenter-ntp`) carry a
`{# BEGIN-KB-METADATA ... END-KB-METADATA #}` Jinja comment linking the state
to the real Broadcom KB article that motivated it (id/title/description/url).
This is optional — only add it where a genuine KB reference exists.

## Resources

All resources are Pillar-based (see above); the "Standalone?" column flags
the resources that need Pillar data to render/behave correctly. Several
resources have no dedicated `vcf_*` state yet and bridge a mutating
execution-module function via Salt's generic `module.run` — see **Module.run
bridges** below for which of those are actually safe to re-run.

| Resource | State module | Standalone? |
|---|---|---|
| `cluster-config/` | `vcf_cluster_config.profile_value` | Yes |
| `cluster-drs/` | `vcf_vim_cluster_config.drs` | Yes |
| `cluster-ha/` | `vcf_vim_cluster_config.ha` | Yes |
| `cluster-resource-pool/` | `vcf_vccluster_resource_pool.shares` | Yes |
| `cluster-vlcm/` | `vcf_esxi_vlcm.depot_configured`/`image_configured`/`policy_configured`/`compliance_checked`/`prechecked`/`staged`/`remediated`/`reported` | Yes |
| `cluster-vsan/` | `vcf_vsan_cluster.configured` | Yes |
| `dvs-pg-vccluster/` | `vcf_vim_dvs.portgroup_present` | **No — Pillar required** |
| `esxi-buffer-size/` | `vcf_esxi_advanced.setting` | Yes |
| `esxi-config/` | `vcf_esxi_ntp.servers` / `vcf_esxi_advanced.setting` / `vcf_esxi_syslog.servers` / `vcf_esxi_service.running` / `vcf_esxi_firewall.rule_enabled` / `vcf_vim_host_dns.config` | Yes |
| `esxi-kernel-module/` | `vcf_vim_host_kernel_module.options_set` | Yes |
| `esxi-shell-access/` | module.run → `vcf_vim_host_security.lockdown_set` | Yes |
| `guest-vm-vccluster/` | `vcf_vim_vm.present` | Yes |
| `installer-depot/` | module.run → `vcf_vcenter_lcm_depot.create_offline` | Yes |
| `log-forwarder/` | `vcf_vcenter_appliance.logging_forwarding` | Yes |
| `nsx-edge-cluster/` | module.run → `vcf_nsx_edge_cluster.create` | Yes |
| `nsxt-dhcp/` | module.run → `vcf_nsx_dhcp.server_create` + `relay_create` | Yes |
| `nsxt-firewall-policy/` | `vcf_nsx_security_policy.present` + `vcf_nsx_firewall_rule.present` | Yes |
| `nsxt-role-binding/` | `vcf_nsx_role_binding.present` | Yes |
| `nsxt-segment/` | `vcf_nsx_segment.present` | Yes |
| `nsxt-tier0/` | `vcf_nsx_tier0.bgp_enabled` / `ospf_enabled` / `multicast_enabled` | Yes (toggles an *existing* gateway only — see note) |
| `nsxt-tier1/` | `vcf_nsx_tier1.multicast_enabled` | Yes (toggles an *existing* gateway only — see note) |
| `permission/` | `vcf_vim_permission.present` | Yes |
| `permission-vccluster/` | `vcf_vim_permission.present` | Yes |
| `role/` | `vcf_vim_role.present` | Yes |
| `sddc-bringup/` | `vcf_installer_bringup.complete` | Yes |
| `sddc-bundles/` | module.run → `vcf_sddc_bundles.upload` | Yes |
| `sddc-domain/` | `vcf_sddc_domain.present` | Yes |
| `sddc-host/` | `vcf_sddc_host.commissioned` | Yes |
| `sddc-manager-feature/` | `vcf_sddc_manager.ready` | Yes |
| `sddc-manager-local-accounts/` | `vcf_sddc_manager_local_accounts.audited` | Yes |
| `sddc-personality/` | module.run → `vcf_sddc_personalities.create` | Yes |
| `sddc-removal/` | `vcf_sddc_host.decommissioned` + `vcf_sddc_domain.absent` | Yes |
| `sddc-users/` | module.run → `vcf_sddc_system.add_users` | Yes |
| `vc-ad-domain/` | `vcf_vcenter_ad_domain.ad_joined` | Yes |
| `vc-advanced-option/` | `vcf_vcenter_advanced_option.advanced_option` | Yes |
| `vc-content-library/` | `vcf_vcenter_content_library.present` | Yes |
| `vc-custom-attribute/` | `vcf_vcenter_custom_attribute.present` | Yes |
| `vc-dns/` | `vcf_vcenter_appliance.dns_servers` | Yes |
| `vc-drs-group-absent/` | `vcf_vim_drs_rule.group_absent` | Yes |
| `vc-drs-host-group/` | `vcf_vim_drs_rule.host_group` | Yes |
| `vc-drs-vm-group/` | `vcf_vim_drs_rule.vm_group` | Yes |
| `vc-drs-vm-host/` | `vcf_vim_drs_rule.vm_host` | Yes |
| `vc-dvs-nioc/` | `vcf_vcenter_dvs_nioc.nioc_enabled` | Yes |
| `vc-dvs-nioc-vccluster/` | `vcf_vcenter_dvs_nioc_vccluster.nioc_enabled` | Yes |
| `vc-dvs-portgroup/` | `vcf_vim_dvs.portgroup_present` + `portgroup_absent` | Yes (⚠ see note) |
| `vc-ntp/` | `vcf_vcenter_appliances.ntp_servers` | Yes |
| `vc-patch/` | `vcf_vc_patch.repository_configured` / `update_prepared` / `update_installed` | **Partial — `sso_password` has no default** |
| `vc-shell/` | `vcf_vcenter_shell.shell_access` | Yes |
| `vccluster-evc/` | `vcf_vim_cluster_evc.mode` | Yes |
| `vccluster-vm-vm-affinity/` | `vcf_vim_drs_rule.vm_affinity` | Yes |
| `vcenter-identity-source/` | module.run → `vcf_vcenter_sso.providers_create` | Yes |
| `vcenter-nkp/` | module.run → `vcf_vcenter_kms.create` | Yes |
| `vcenter-ntp/` | `vcf_vcenter_appliances.ntp_servers` | Yes |
| `vcenter-service/` | module.run → `vcf_vcenter_appliance.services_start` | Yes |
| `vcenter-sso-group/` | module.run → `vcf_vcenter_sso.groups_create` | Yes |

## Module.run bridges

9 resources have no dedicated `vcf_*` state yet and instead bridge a
mutating execution-module function directly via Salt's generic `module.run`.
Where the underlying API exposes a clean existence check, the `.sls` wires
an `unless:` guard so re-applying is a true no-op. Where it doesn't, the
`.sls` carries a comment saying so — re-running it either just re-asserts
the same value (safe in effect, even though `module.run` won't report
`changes == {}` the way a real state would) or, for anything that creates a
new object with a server-generated id, will create a **duplicate** each time.

| Resource | Idempotent on re-run? |
|---|---|
| `sddc-personality/` | Yes — guarded (`unless: vcf_sddc_personalities.list_`) |
| `vcenter-sso-group/` | Yes — guarded (`unless: vcf_vcenter_sso.groups_get_or_none`) |
| `esxi-shell-access/` | Safe in effect (re-asserts the same lockdown mode), not diffed |
| `vcenter-service/` | Safe in effect (starting an already-running service is a no-op server-side), not diffed |
| `installer-depot/` | **No** — no existence check; re-running attempts creation again |
| `nsx-edge-cluster/` | **No** — server-generated id, no existence check |
| `nsxt-dhcp/` | **No** — `server_get`/`relay_get` raise on 404 rather than returning `None`, so no safe guard is possible without adding one yourself |
| `sddc-bundles/` | **No**, and not meant to be — bundle upload is a one-shot action, not a "present" resource |
| `sddc-users/` | **No** — no caller-supplied id, no existence check before bulk-adding |
| `vcenter-identity-source/` | **No** — server-generated id, no existence check; re-running creates a duplicate LDAP identity source |
| `vcenter-nkp/` | **No** — server-generated id, no existence check |

## Known issues

- **`vc-dvs-portgroup/vc-dvs-portgroup.sls` runs both states on every
  apply.** Its comment calls `portgroup_present` and `portgroup_absent`
  "mutually exclusive examples," but Salt has no concept of that — it runs
  every declared state ID in the file regardless of comments. As written,
  every `state.apply` on this resource creates the port-group and then
  immediately deletes it in the same run. Treat this one as two separate
  illustrative snippets to copy from individually, not as a runnable example
  on its own; a real fix would split it into two files or gate one state
  behind a Jinja conditional.
- **`vc-patch/`'s `sso_password` has no default in `defaults.yaml`.**
  `map.jinja` reads it as a bare top-level Pillar key (`cfg.sso_password`,
  not nested under any section), so applying this resource standalone
  renders with an empty password — Pillar data supplying `sso_password` is
  required for `update_installed` to actually work against a real vCenter.
- **`nsxt-tier0/` and `nsxt-tier1/` only toggle settings on an *existing*
  gateway** — `vcf_nsx_tier0`/`vcf_nsx_tier1` don't create a Tier-0/Tier-1
  gateway or configure interfaces (no such function exists yet), so these
  examples assume the named gateway is already provisioned.
- **`vc-ntp/` and `vcenter-ntp/` drive the same state module**
  (`vcf_vcenter_appliances.ntp_servers`) — `vcenter-ntp/` additionally
  documents its motivating KB article. Consider consolidating on one of the
  two.

## Testing

Live coverage for this tree lives in the sibling `saltext-vcf-integration`
repo, under `tests/vcf_infra/` — one test file per resource here, run via a
real `salt-call state.sls`/`state.show_sls` against these actual
`.sls`/`map.jinja`/`defaults.yaml` files (not the Python state module in
isolation). Resources safe to fully create/delete get a full lifecycle test;
resources that only configure existing shared infra get an idempotency-only
check that reads the live current value before asserting a no-op; one-shot
or hard-to-reverse resources (patching, host commission, bringup, bundle
upload, AD domain join, KMS/identity-source creation) are covered
render-only via `state.show_sls` and are never executed.

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
   `dvs-pg-vccluster/` (marked "No" above), Pillar data for
   `dvs.name`/`portgroup.name`/`portgroup.vlan_id` is required — it has no
   standalone default. For `vc-patch/` (marked "Partial" above), Pillar data
   for `sso_password` is required for the resource to actually work, even
   though it renders without it.
3. Apply the state, e.g.:

   ```bash
   salt '<minion>' state.apply cluster-config.cluster-config saltenv=<your-env> pillar='{"cluster-config": {"cluster": {"name": "domain-c9"}}}' test=true
   ```

   (or rely on Pillar already assigned to the target via `pillar_roots`/an
   external pillar source, in which case the inline `pillar=` argument above
   isn't needed). Run with `test=true` first to preview the change, then
   without it to apply for real.
