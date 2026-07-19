# vCenter examples

## Inventory

```bash
salt-call vcf_vcenter_cluster.list_
salt-call vcf_vcenter_host.list_
salt-call vcf_vcenter_vm.list_
salt-call vcf_vcenter_datacenter.list_
salt-call vcf_vcenter_datastore.list_
salt-call vcf_vcenter_network.list_
salt-call vcf_vcenter_storage_policy.list_
```

## VM lifecycle (REST)

```bash
salt-call vcf_vcenter_vm.get vm-100
salt-call vcf_vcenter_vm.power_on vm-100
salt-call vcf_vcenter_vm.power_off vm-100
salt-call vcf_vcenter_vm.reset vm-100
```

## VM snapshots (SOAP)

REST has no snapshot surface in VCF 9.x; snapshots route through pyVmomi.

```bash
salt-call vcf_vim_vm_snapshot.list_ vm-100
salt-call vcf_vim_vm_snapshot.current vm-100

salt-call vcf_vim_vm_snapshot.create vm-100 baseline \
    description="pre-upgrade" memory=true quiesce=true

salt-call vcf_vim_vm_snapshot.revert vm-100 baseline
salt-call vcf_vim_vm_snapshot.remove vm-100 baseline
salt-call vcf_vim_vm_snapshot.remove_all vm-100
```

## Tagging

```bash
salt-call vcf_vcenter_tag.list_
salt-call vcf_vcenter_tag.create production category-1 description="Prod fleet"
salt-call vcf_vcenter_tag.assign urn:vmomi:Tag:prod VirtualMachine vm-100
salt-call vcf_vcenter_tag.list_assigned VirtualMachine vm-100
```

## Cluster Configuration Profile (vSphere 9)

Desired-state profile API. Replaces direct ESXi REST when hosts are
vCenter-managed.

```bash
salt-call vcf_cluster_config.get_profile domain-c9
salt-call vcf_cluster_config.draft_create domain-c9 spec='{...}'
salt-call vcf_cluster_config.draft_preview domain-c9 draft_id=...
salt-call vcf_cluster_config.draft_apply  domain-c9 draft_id=...
salt-call vcf_cluster_config.check_compliance domain-c9
```

## Appliance

```bash
salt-call vcf_vcenter_appliance.version
salt-call vcf_vcenter_appliance.health_system
salt-call vcf_vcenter_appliance.services_list
salt-call vcf_vcenter_appliance.dns_get
salt-call vcf_vcenter_appliance.logging_forwarding_get
```

## KMS providers

```bash
salt-call vcf_vcenter_kms.list_
salt-call vcf_vcenter_kms.get my-kms
salt-call vcf_vcenter_kms.create '{"provider":"my-kms","type":"NATIVE", ...}'
```

## ESXi Lifecycle (vLCM patching)

Patch ESXi hosts in a vSphere cluster: depot → desired image → policy →
compliance/precheck/stage/remediate. Same `vcenter` pillar connection as
the rest of this page — no separate credentials needed.

```bash
salt-call vcf_esxi_vlcm.offline_depot_create '{"location": "http://repo.example.com/depot.zip"}'
salt-call vcf_esxi_vlcm.depot_sync

salt-call vcf_esxi_vlcm.desired_image_get domain-c9
salt-call vcf_esxi_vlcm.draft_import_software_spec domain-c9 '{"base_image": {"version": "9.2.0.0.25504872"}}'
salt-call vcf_esxi_vlcm.draft_commit domain-c9 draft-1

salt-call vcf_esxi_vlcm.compliance_scan domain-c9
salt-call vcf_esxi_vlcm.remediate domain-c9
```

Declaratively, via `vcf_esxi_vlcm` states:

```yaml
patch-depot:
  vcf_esxi_vlcm.depot_configured:
    - location: http://repo.example.com/VMware-ESXi-9.2.0.0.25504872-depot.zip

domain-c9:
  vcf_esxi_vlcm.image_configured:
    - image_spec:
        base_image:
          version: "9.2.0.0.25504872"
    - require:
      - vcf_esxi_vlcm: patch-depot
  vcf_esxi_vlcm.remediated:
    - require:
      - vcf_esxi_vlcm.image_configured: domain-c9
```

## VC Patch (VCSA self-update)

Patches the vCenter Server Appliance itself via its VAMI appliance-update
API — a distinct workflow from ESXi/NSX/SDDC Manager patching. Same
`vcenter` pillar connection as the rest of this page.

```bash
salt-call vcf_vc_patch.get_update_policy
salt-call vcf_vc_patch.list_pending_updates

# Stage without monitoring on flaky links, then poll separately
salt-call vcf_vc_patch.stage 9.0.1.0.12345 monitor=false
salt-call vcf_vc_patch.get_update_status
salt-call vcf_vc_patch.get_staged_update

# Install (requires the SSO admin password)
salt-call vcf_vc_patch.install 9.0.1.0.12345 'VMware123!VMware123!'
```

Declaratively, via `vcf_vc_patch` states:

```yaml
vc-repo:
  vcf_vc_patch.repository_configured:
    - repository_url: http://repo.example.com/vcsa/

vc-staged:
  vcf_vc_patch.update_prepared:
    - version: "9.0.1.0.12345"
    - require:
      - vcf_vc_patch: vc-repo

vc-installed:
  vcf_vc_patch.update_installed:
    - version: "9.0.1.0.12345"
    - sso_password: {{ pillar['vc_sso_password'] }}
    - require:
      - vcf_vc_patch: vc-staged
```
