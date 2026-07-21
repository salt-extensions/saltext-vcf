The changelog format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

This project uses [Semantic Versioning](https://semver.org/) - MAJOR.MINOR.PATCH

# Changelog

## 1.1.0 (2026-07-21)


### Fixed

- Fix a batch of bugs surfaced when the ``vcf_esxi_*`` state modules are applied against a real ESXi 9.1 host (build 25370933) instead of the in-memory mocks used by the test suite: ``utils/esxi.get_host_system`` traversal, ``esxi_ntp.get`` property access, and ``esxi_advanced.get`` return shape.
- Make ``vcf_esxi_firewall``, ``vcf_esxi_service``, and ``vcf_vim_host_network.vswitch_present`` cleanly idempotent so re-applying against an already-converged host produces zero changes. Adds a new ``vcf_esxi_firewall.global_enabled`` state (maps to ``HostFirewallSystem.UpdateDefaultPolicy``), renames the service-policy key to match the client, and stops treating ``num_ports`` as drift when ESXi auto-scales it.
- Make ``vcf_vim_vm.present`` parallel-safe (needed when a lab brings up 4 nested VMs concurrently via ``state.orchestrate``) and route standalone-ESXi datastore uploads through the correct endpoint.
- ``vim_vm_nic.add`` now falls back to a ``deviceName``-only NIC backing when the port group has no ``vim.Network`` MO (which is the case for standalone-ESXi port groups that only carry VMkernel traffic). ESXi resolves the port group by name at attach time.


### Added

- Add ``vim_vm_cdrom`` client + ``vcf_vim_vm_cdrom`` execution/state modules for CD-ROM device lifecycle (add, remove, attach ISO, detach), including the pyVmomi task-wait helper needed by ``state.apply`` orchestration of a nested-ESXi lab.
- Add `esxi_vlcm` client, `vcf_esxi_vlcm` execution module, and `vcf_esxi_vlcm` state module for patching ESXi hosts via vCenter's ESX Lifecycle Manager (vLCM) REST API: depot configuration/sync, desired-image drafts, cluster apply policy, and compliance/precheck/stage/remediate workflows.
- Add `vc_patch` client, `vcf_vc_patch` execution module, and `vcf_vc_patch` state module for patching the vCenter Server Appliance itself via VAMI's appliance-update REST API: repository policy configuration, idempotent staging (with version resolution and stage-timeout/precheck-retry recovery), monitoring, and install.
- Add the SDDC Manager REST surface needed to drive VCF async patching directly (without shelling out to the ``vcf-async-patch-tool`` CLI): ``sddc_bundles.upload`` / ``delete`` / ``for_skip_upgrade`` for offline bundle staging, ``sddc_releases.custom_patches`` for reading which async patches are registered on a domain, and a new ``sddc_personalities`` client + ``vcf_sddc_personalities`` execution module for vSphere cluster-image lifecycle. The enable/disable half of the async-patch workflow and the orchestrating state module are left as follow-ups pending lab reverse-engineering of the ``vcf-async-patch-tool -e --patch`` traffic.
- Extend ``vcf_vim_datastore_file.file_present`` with ``force`` and ``match_size`` options so a re-run of ``state.apply`` re-uploads a file whose size differs from the local source or when the caller wants an unconditional overwrite (useful for iterating on nested-lab ISO builds).
- Extend `vcfops_resource_group` with `members(group_id)` and `list_types()` for the corresponding VCF Operations endpoints.
- New ``vcf_vim_host_datastore`` state module (``vmfs_present``, ``nfs_mounted``, ``absent``) wrapping the existing execution module so a VMFS datastore can be declared in a Salt state file — standalone-aware and vCenter-aware.
- New ``vcf_vim_vm`` state module for VM lifecycle (``present`` / ``absent`` / ``power_*``) against a standalone ESXi host, alongside port-group security-policy support (``promiscuous`` / ``mac_changes`` / ``forged_transmits``) on ``vim_host_network`` for nested-VM labs.
- Route every ``vim_*`` client through a shared ``utils/vim.resolve_host_system`` helper so state modules can target a standalone ESXi host with only the ``saltext.vcf.esxi`` pillar (no vCenter present). Detection is automatic based on which pillar block is populated; the vCenter path is unchanged.

## 1.0.0 (2026-06-07)


### Breaking changes

- Renamed project from ``saltext-vmware`` to ``saltext-vcf``. The PyPI distribution, GitHub repository, and Python import path (``saltext.vmware`` -> ``saltext.vcf``) all change. Salt loader module names also rename from ``vmware_*`` to ``vcf_*`` (e.g. ``vmware_vcenter_appliance`` -> ``vcf_vcenter_appliance``); update any state, pillar, or CLI references accordingly. VMware-defined identifiers (``vmware_accepted`` / ``vmware_certified`` VIB acceptance levels, ``vmware_soap_session`` cookie, ``vmware-api-session-id`` header, ``pyvmomi``, ``vmware-vcenter``/``vmware-vcf`` PyPI dependencies) are unchanged.


### Removed

- Removed the ``installer_credentials``, ``installer_logs``, and ``installer_system`` clients and execution modules. Their ``/v1/system/security/passwords`` / ``/v1/system/log-bundles`` / ``/v1/system/*`` endpoints did not exist on the actual VCF Installer build; ``installer_bringup`` and ``fleet_password`` remain as the verified installer-side surfaces.


### Changed

- ESXi standalone clients (``esxi_advanced``, ``esxi_firewall``, ``esxi_host``, ``esxi_ntp``, ``esxi_service``, ``esxi_syslog``) and ``utils/esxi`` now use pyVmomi SOAP (``SmartConnect`` / ``/sdk``) instead of REST ``/api/session``. Shuttle-deployed lab hosts omit the vAPI endpoint entirely, and ESXi joined to vCenter blocks ``/api/session`` with HTTP 400; SOAP is the universally available surface. The execution-module names and dunder keys (``vcf_esxi_*``) are unchanged.


### Fixed

- Fix several vCenter 9 / VCF 9 REST body shapes discovered against the live lab: ``vcenter_content_library.update_session_add_file`` now uses the path-style ``/api/content/library/item/update-session/{session_id}/file?action=add`` (the legacy POST ``/updatesession/file`` shape 404s on vSphere 9); ``vcenter_content_library.create_local`` / ``create_subscribed`` send the spec at the root (no more ``create_spec`` wrapper); ``vcenter_appliance.dns_set`` / ``logging_forwarding_set`` use PUT (PATCH returns 405); ``sddc_certificates.create_csrs`` sends ``{csrGenerationSpec, resources}`` instead of a flat list.
- VDS and DPG (Distributed Port Group) lifecycle mutators (``vim_dvs.create``/``reconfigure``/``delete``/``add_host``/``remove_host``, ``vim_dvs_portgroup._add``/``reconfigure``/``delete``) now wait on the underlying pyVmomi ``*_Task`` before returning. A shared ``utils/vim.wait_for_task`` helper drives the wait. Previously callers raced the task and ``list_()`` could return a stale view immediately after a successful-looking create.
- ``nsx_ipsec_vpn.create_ike_profile`` / ``create_tunnel_profile`` / ``create_dpd_profile`` now auto-inject the appropriate ``resource_type`` (``IPSecVpnIkeProfile`` / ``IPSecVpnTunnelProfile`` / ``IPSecVpnDpdProfile``) so NSX 9 stops rejecting the PUT with HTTP 400. Callers can still override via ``resource_type=`` in the spec.


### Added

- Added a ``CLI Example:`` doc-example harness: ``tests/_doc_examples`` parses every ``salt '*' <mod>.<func> ...`` line out of module docstrings and exposes them to two passes. ``tests/unit/test_doc_examples`` is a signature-check pass that asserts the virtual module name resolves and the documented args bind to the function. The companion saltext-vcf-integration repo runs the same parsed examples against a live VCF lab.
- Bootstrap the VCF Installer onto a bare ESXi host via pyVmomi OVF deploy. ``clients/ovf_deploy`` adds a tarball-parse + ``OvfManager.CreateImportSpec`` + ``HttpNfcLease`` PUT pipeline (with vmware_soap_session cookie + ``Overwrite: t`` header so ESXi's ha-nfc daemon authorizes the upload), a streaming HTTPS PUT for multi-GB VMDKs, and ``wait_for_task``-driven power-on. State module ``vcf_installer_appliance`` exposes this as a declarative ``installer.running`` workflow.
- New topology + tooling clients: ``automation_topology`` (cross-component view of a VCF Automation deployment), ``installer_topology`` (introspects the bringup spec / running installer), and ``ovftool_deploy`` (subprocess wrapper around ``ovftool`` for callers that prefer it over the pure-pyVmomi path).
- The vCenter per-request HTTP timeout is now configurable. ``utils/vcenter.api_*`` helpers accept an optional ``timeout=`` kwarg; the default is also tunable via the ``saltext.vcf.vcenter.timeout`` pillar key. ``vcenter_content_library.ovf_deploy`` defaults to ``timeout=1800`` (30 min) so OVF deploys no longer race the previous hard-coded 30 s read timeout.
- VCF Automation (VCFA / Aria Automation 9.x) end-to-end integration: new ``utils/vcfa`` with two-step CSP refresh-token auth, per-(host,user) token cache, transparent bearer re-mint on 401, configurable per-request timeout, multipart helper, and a ``wait_for_deployment`` poller. Eighteen new client / execution-module pairs cover cloud accounts, cloud zones, storage profiles, network profiles, projects, project users, cloud templates (blueprint versions), policies, catalog (items + sources), vRO packages, vRO configuration elements, workflow runs, ABX actions, action secrets, action subscriptions, resource actions, IAM role bindings, and custom roles.
- VCF Operations fleet certificate management: new ``vcfops_fleet_certificates`` client + module covering the fleet-wide certificate inventory, renewal scheduling, and rotation operations exposed by VCF Operations (separate from the truststore surface in ``vcfops_certificate``). Contributed by `Denys Aleksandrov <https://github.com/denysaleksandrov>`_.
- VCF Operations fleet password and certificate surfaces: new ``vcfops_fleet_passwords`` (the VCF 9.x replacement for the SDDC-Manager-backed ``fleet_password``) wraps ``/suite-api/api/fleet-management/password-management`` with paginated ``list_``, ``get_account``, ``update``, and a ``check_expiry(threshold_days=90)`` helper that buckets accounts into ``ok`` / ``expiring`` / ``noExpiry`` with ISO-rendered expiry dates. New ``vcfops_certificate`` wraps the VCF Ops truststore (``/suite-api/api/certificate``) for list / get / delete by thumbprint.

## 0.1.0 (2026-05-14)


### Added

- VCF Installer (formerly Cloud Builder) support: utils + clients for system/bringup/credentials/logs, modules, declarative bringup state, plus live lab spin-up/teardown coverage in the integration repo. [#3](https://github.com/salt-extensions/saltext-vcf/issues/3)
