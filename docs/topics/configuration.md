# Configuration

All connection details live under `saltext.vmware` in pillar, one
block per component.

```yaml
saltext.vmware:
  vcenter:
    host: mgmt-vc.example.com
    username: administrator@vsphere.local
    password: VMware123!VMware123!
    verify_ssl: false
  sddc_manager:
    host: sddc-manager.example.com
    username: administrator@vsphere.local
    password: VMware123!VMware123!
    verify_ssl: false
  nsx:
    host: mgmt-nsx.example.com
    username: admin
    password: VMware123!VMware123!
    verify_ssl: false
  vcf_ops:
    host: ops.example.com
    username: admin
    password: VMware123!VMware123!
    auth_source: LOCAL          # optional, default LOCAL
    verify_ssl: false
  esxi:
    host: esxi01.example.com    # standalone hosts only
    username: root
    password: VMware123!
    verify_ssl: false
```

## Per-component

| Block | Auth | Used by |
|---|---|---|
| `vcenter` | `POST /api/session` → session token | `vmware_vcenter_*`, `vmware_vsan_*`, `vmware_vim_*` |
| `sddc_manager` | `POST /v1/tokens` → bearer JWT | `vmware_sddc_*`, `vmware_vcf_services` |
| `nsx` | HTTP Basic | `vmware_nsx_*` (Policy + Management APIs) |
| `vcf_ops` | `POST /suite-api/api/auth/token/acquire` → `Authorization: vRealizeOpsToken <token>` | `vmware_vcfops_*` |
| `esxi` | `POST /api/session` (same shape as vCenter) | `vmware_esxi_*` |

Session tokens cache per `(host, username)` for the Python process
lifetime. Call `<util>.invalidate_session(opts)` to force re-auth.

The `esxi` block applies only to direct-mode hosts. vCenter-managed
ESXi has its direct REST locked; use `vmware_cluster_config` (Cluster
Configuration Profile API) instead.

For `vcf_ops`, override `auth_source` when authenticating against a
non-local IdP source.

## Profiles

`profile=<name>` selects a named override under
`saltext.vmware.profiles.<name>`:

```yaml
saltext.vmware:
  vcenter:
    host: mgmt-vc-prod.example.com
    username: administrator@vsphere.local
    password: prod-pass
  profiles:
    staging:
      vcenter:
        host: mgmt-vc-staging.example.com
        username: administrator@vsphere.local
        password: staging-pass
```

```bash
salt-call vmware_vcenter_cluster.list_
salt-call vmware_vcenter_cluster.list_ profile=staging
```

## Multi-instance fleets

For minions managing more than one of any component, use the Resources
framework instead:

```yaml
resources:
  vcenter:
    instances:
      mgmt-vc:
        host: mgmt-vc.example.com
        username: administrator@vsphere.local
        password: secret
      prod-vc:
        host: prod-vc.example.com
        username: administrator@vsphere.local
        password: other-secret
```

See [Resources Framework](resources-framework.md).

## Security

- Source pillar from a secret store (gpg/Vault/SOPS). Salt does not
  encrypt pillar at rest.
- `profile=` resolves from pillar at call time; no env-var or external
  secret-store fallback.
- Tokens cache in-process. Restart the minion or call
  `invalidate_session(opts)` on the relevant util to clear.
