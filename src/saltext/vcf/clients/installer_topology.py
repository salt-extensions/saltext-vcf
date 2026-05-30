"""Validation helpers for VCF Installer workflow pillar data."""


def validate(spec):
    """Validate the local ``saltext.vcf`` workflow pillar shape.

    This is intentionally structural. The VCF Installer API remains the source
    of truth for deep bringup validation; this catches local wiring mistakes
    before a long OVA upload or Installer validation run.
    """
    root = spec or {}
    errors = []
    warnings = []

    appliance = root.get("installer_appliance") or {}
    bringup = root.get("bringup_spec") or {}
    _validate_appliance(appliance, errors, warnings)
    _validate_bringup(bringup, appliance, errors, warnings)

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def _validate_appliance(appliance, errors, warnings):
    required = (
        "installer_host",
        "installer_ova_url",
        "installer_vm_name",
        "installer_deploy_esxi",
    )
    for key in required:
        if not appliance.get(key):
            errors.append(f"installer_appliance.{key} is required")

    hosts = appliance.get("esxi_hosts") or []
    if not hosts:
        errors.append("installer_appliance.esxi_hosts must contain at least one host")
    target = appliance.get("installer_deploy_esxi")
    if target and not _host_entry(hosts, target):
        errors.append(
            "installer_appliance.installer_deploy_esxi must match an esxi_hosts "
            f"entry by fqdn or ip (got {target!r})"
        )

    backend = (appliance.get("deployment_backend") or "pyvmomi").lower()
    if backend not in ("pyvmomi", "ovftool"):
        errors.append(
            "installer_appliance.deployment_backend must be 'pyvmomi' or 'ovftool' "
            f"(got {backend!r})"
        )
    if backend == "ovftool":
        if not appliance.get("datastore"):
            warnings.append("ovftool backend should specify installer_appliance.datastore")
        if appliance.get("disk_provisioning") != "thin":
            warnings.append(
                "ovftool backend should use installer_appliance.disk_provisioning: thin "
                "for the VCF Installer OVA"
            )


def _validate_bringup(bringup, appliance, errors, warnings):
    if not bringup:
        errors.append("bringup_spec is required")
        return

    for key in ("sddcId", "workflowType", "dnsSpec", "hostSpecs"):
        if not bringup.get(key):
            errors.append(f"bringup_spec.{key} is required")

    host_specs = bringup.get("hostSpecs") or []
    if len(host_specs) < 3:
        errors.append("bringup_spec.hostSpecs must contain at least three ESXi hosts")

    appliance_hosts = appliance.get("esxi_hosts") or []
    known_names = _known_host_names(appliance_hosts)
    for idx, host in enumerate(host_specs):
        hostname = host.get("hostname")
        if not hostname:
            errors.append(f"bringup_spec.hostSpecs[{idx}].hostname is required")
            continue
        if known_names and hostname not in known_names:
            warnings.append(
                f"bringup_spec.hostSpecs[{idx}].hostname {hostname!r} does not match "
                "installer_appliance.esxi_hosts short name, fqdn, or ip"
            )
        creds = host.get("credentials") or {}
        if not creds.get("username") or not creds.get("password"):
            errors.append(
                f"bringup_spec.hostSpecs[{idx}].credentials.username/password are required"
            )

    dns = bringup.get("dnsSpec") or {}
    if dns and (not dns.get("subdomain") or not dns.get("nameservers")):
        errors.append("bringup_spec.dnsSpec.subdomain and nameservers are required")

    for key in ("sddcManagerSpec", "vcenterSpec", "nsxtSpec", "datastoreSpec", "clusterSpec"):
        if not bringup.get(key):
            errors.append(f"bringup_spec.{key} is required")

    networks = {n.get("networkType") for n in bringup.get("networkSpecs") or []}
    for network_type in ("MANAGEMENT", "VMOTION", "VSAN"):
        if network_type not in networks:
            errors.append(f"bringup_spec.networkSpecs must include {network_type}")


def _host_entry(hosts, value):
    for host in hosts:
        if value in (host.get("fqdn"), host.get("ip")):
            return host
    return None


def _known_host_names(hosts):
    names = set()
    for host in hosts:
        fqdn = host.get("fqdn")
        ip = host.get("ip")
        if fqdn:
            names.add(fqdn)
            names.add(fqdn.split(".", 1)[0])
        if ip:
            names.add(ip)
    return names
