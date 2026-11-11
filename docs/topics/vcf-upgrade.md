# VCF upgrades through SDDC Manager

`vcf_upgrade` ports the standalone `saltext_vcf_automation` lifecycle workflow
into `saltext.vcf`. Like `vcf_vc_patch`, it separates API clients, execution
functions, and declarative states. It manages SDDC Manager upgrades and the
NSX/vCenter/HOST draft workflow through SDDC Manager; `vcf_vc_patch` continues
to manage vCenter appliance updates through VAMI.

The implementation has local API simulation and regression coverage. Target
VCF builds and a live upgrade have **not** been validated. Verify captured
request fields against the API schema of your exact source and target builds.

## Configuration

Use the existing SDDC Manager connection pillar. Load credentials from your
secret backend. HTTPS certificate verification defaults to true; install the
appropriate CA trust on the minion.

```yaml
saltext.vcf:
  sddc_manager:
    host: sddc-manager.example.test
    username: administrator@vsphere.local
    # password: supply through an encrypted pillar/secret backend
    verify_ssl: true
  vcf_upgrade:
    # Illustrative value: replace with a discovered, supported exact build.
    target_build: "9.1.0-12345678"
    component_type: SDDC_MANAGER
    # domain_id: optional; otherwise resolve the MANAGEMENT domain
    lifecycle:
      bundle_timeout_seconds: 14400
      precheck_timeout_seconds: 7200
      upgrade_timeout_seconds: 43200
      poll_interval_seconds: 60
```

All execution functions accept `profile=<name>` to select the existing
`saltext.vcf:profiles:<name>:sddc_manager` connection. Upgrade settings remain
under the common `saltext.vcf:vcf_upgrade` key. The checkpoint defaults to
`<Salt cachedir>/vcf-upgrade.json`; use one shared checkpoint for concurrent
calls concerning the same upgrade. Do not mix standalone and ported workers.

## Discover, preview, and execute

```bash
salt-call vcf_upgrade.list_target_versions min_bump=ANY
salt-call vcf_upgrade.list_bundle_builds 9.1.0.0
salt-call vcf_upgrade.run dry_run=true
salt-call state.single vcf_upgrade.upgraded name=management-upgrade test=true
salt-call state.single vcf_upgrade.upgraded name=management-upgrade
```

Release discovery lists candidates. It does not establish a supported upgrade
path; confirm that against the source and target release documentation.
The state downloads the selected bundle, creates the upgrade, polls completion,
and verifies inventory against the bundle's **per-component** target version.
It rejects ambiguous builds, unrelated HOST clusters, and failed prechecks.
Read-only states and dry runs submit no upgrades or checkpoint writes. A dry run
still needs API access and valid configuration; it does not run actual prechecks.

SDDC Manager creation uses `draftMode=false` and commits execution timing
immediately. Calling `create_upgrade` or its state for SDDC Manager can start
the upgrade. NSX, vCenter, and HOST use drafts, check-set selection and polling,
then execution. `execute_upgrade` is an explicit low-level commit operation;
use `upgraded`/`sequence_completed` to enforce the automatic precheck workflow.

## Explicit component sequencing

Set `saltext.vcf:vcf_upgrade:sequence` to the order approved for your release
and environment. There is no implicit whole-VCF sequence. Each entry can use
its own `target_build`, `domain_id`, and `options`.

```yaml
saltext.vcf:
  vcf_upgrade:
    sequence:
      - type: NSX_T_MANAGER
        target_build: "9.1.0-12345678"
        options:
          nsx_mp_upgrade: true
          nsx_datapath_appliance_upgrade: false
      - type: VCENTER
        target_build: "9.1.0-12345678"
        options:
          vcenter_upgrade_mechanism: InPlace
      - type: HOST
        target_build: "9.1.0-12345678"
        clusters:
          - name: management
            cluster_id: REPLACE_CLUSTER_UUID
            personality_id: REPLACE_IMPORTED_PERSONALITY_UUID
```

The NSX defaults perform an MP-only upgrade, following the supplied capture;
this does not establish that the NSX datapath has been upgraded. HOST requires
an already imported, compatible personality. Personality import remains a
separate prerequisite. vCenter temporary networking supports `AUTOMATIC` only.
Component options are passed in the `options` dictionary, not as connection
keywords.

```bash
salt-call state.single vcf_upgrade.sequence_completed name=vcf-lifecycle test=true
salt-call state.single vcf_upgrade.sequence_completed name=vcf-lifecycle
```

With `vcf-infra/` in file roots, `state.apply vcf-upgrade.vcf-upgrade` provides
the same single/sequence dispatch. `schedule_for_later` requires a timestamp;
monitoring remains bounded by `upgrade_timeout_seconds`, so a distant schedule
can time out locally without cancelling the remote upgrade.

## Resume and recovery

Rerun with identical endpoint, sequence, domain, targets, and options. Atomic,
restricted-permission checkpoints retain remote upgrade and check-set IDs.
Completed units are skipped after inventory revalidation. Incomplete units
reuse their saved IDs. Precheck failure never causes execution or recreation.
Concurrent calls using the same checkpoint fail before mutation.

A changed request or malformed checkpoint fails closed. `CREATING` and
`PRECHECK_SUBMITTING` mean a request may have reached the server without its
reply being saved. Inspect SDDC Manager before editing the checkpoint: recover
the existing remote ID and transition to `CREATED`/`PRECHECK_RUNNING`, preserving
its domain, bundle, target, draft flag and fingerprint. If a request is proven
not to have been accepted, reconcile the checkpoint deliberately. An uncertain
execution commit that still appears DRAFT also requires reconciliation. Never
reset blindly: populated checkpoints cannot be reset with `reset_checkpoint`.
Archive a checkpoint only after confirming all associated remote work is
complete or explicitly reconciled.

If postvalidation fails because inventory is stale or unhealthy, rerun after
checking the environment. The saved upgrade ID is monitored again; no replacement
upgrade is created. API success verifies completion and inventory version/status,
not application availability, backups, hardware compatibility, or every NSX
transport node. Keep live acceptance checks specific to your environment.
