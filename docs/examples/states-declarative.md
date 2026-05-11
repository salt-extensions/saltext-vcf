# States catalog

One representative example per state module.

## vCenter

```yaml
Cluster:
  vmware_vcenter_cluster.present:
    - name: my-cluster
    - datacenter: my-dc

ESXi host:
  vmware_vcenter_host.present:
    - name: esxi-new.example.com
    - cluster: my-cluster
    - username: root
    - password: '{{ pillar["esxi_pass"] }}'
    - thumbprint: <sha256>

Appliance DNS:
  vmware_vcenter_appliance.dns_servers:
    - name: appliance-dns
    - servers: [10.0.0.1, 10.0.0.2]
    - mode: is_static
```

## NSX

```yaml
Segment:
  vmware_nsx_segment.present:
    - name: tenant-a-web
    - transport_zone_path: /infra/sites/default/enforcement-points/default/transport-zones/<tz-id>
    - subnets:
        - gateway_address: 10.10.0.1/24

Security policy:
  vmware_nsx_security_policy.present:
    - name: tenant-a-policy

Firewall rule (web → db):
  vmware_nsx_firewall_rule.present:
    - name: tenant-a-policy/web-to-db
    - security_policy_id: tenant-a-policy
    - action: ALLOW
    - source_groups: [/infra/domains/default/groups/tenant-a-web]
    - destination_groups: [/infra/domains/default/groups/tenant-a-db]
    - services: [/infra/services/HTTPS]

Role binding:
  vmware_nsx_role_binding.present:
    - name: alice-audit
    - spec:
        name: alice
        type: remote_user
        roles:
          - role: auditor
```

## SDDC Manager

```yaml
Commission ESXi:
  vmware_sddc_host.present:
    - name: esxi-spare-1
    - specs:
        - fqdn: esxi-spare-1.example.com
          username: root
          password: '{{ pillar["esxi_pass"] }}'
          networkPoolName: pool-1
          storageType: VSAN
```

## VCF Operations

```yaml
Local user:
  vmware_vcfops_user.present:
    - name: alice
    - password: '{{ pillar["ops_alice_password"] }}'
    - role_names: [Administrator]

Custom role:
  vmware_vcfops_role.present:
    - name: ReadOnlyMonitor
    - description: View-only dashboards + alerts
    - privilege_keys: [DASHBOARD, METRICS_DASHBOARDS, ALERTS_VIEW]

Adapter credential:
  vmware_vcfops_credential.present:
    - name: vc-prod
    - adapter_kind: VMWARE
    - credential_kind: PRINCIPALCREDENTIAL
    - fields:
        - name: USER
          value: administrator@vsphere.local
        - name: PASSWORD
          value: '{{ pillar["ops_vc_password"] }}'

Super metric:
  vmware_vcfops_supermetric.present:
    - name: rolling-avg-cpu
    - formula: 'avg(${this, metric=cpu|usage_average})'
```

## VMSP

```yaml
Health gate before upgrade:
  vmware_vcf_services.healthy:
    - name: COMMON_SERVICES
```

## VKS

```yaml
TKG activated:
  vmware_vcenter_supervisor_service.activated:
    - name: tkg.vsphere.vmware.com

VM class:
  vmware_vcenter_vm_class.present:
    - name: gpu-medium
    - cpu_count: 8
    - memory_MB: 32768
    - description: 8 vCPU / 32 GiB / GPU passthrough
```

## vSAN

```yaml
Fault domain:
  vmware_vsan_fault_domain.present:
    - name: rack-a
    - cluster: domain-c9
    - hosts: [host-100, host-101]

Cluster config:
  vmware_vsan_cluster.present:
    - name: domain-c9
    - dedup_enabled: true
    - encryption_enabled: true
```

## ESXi (standalone)

Standalone-mode hosts only. For vCenter-managed hosts, use
`vmware_cluster_config`.

```yaml
SSH off:
  vmware_esxi_service.absent:
    - name: TSM-SSH

NTP:
  vmware_esxi_ntp.present:
    - name: ntp-pool
    - servers: [time.example.com]
    - enabled: true

Syslog:
  vmware_esxi_syslog.present:
    - name: ops-forwarding
    - servers: ['udp://syslog.example.com:514']

Firewall rule:
  vmware_esxi_firewall.present:
    - name: sshServer
    - enabled: true
    - allowed_ips: ['10.0.0.0/8']
    - all_ip: false
```

## Cluster Configuration Profile

```yaml
Drift-managed config:
  vmware_cluster_config.applied:
    - name: domain-c9
    - spec_path: /srv/salt/profiles/domain-c9.json
    - apply_policy: SOFTWARE_CONFIGURATION_AND_HOST_REMEDIATION
```
