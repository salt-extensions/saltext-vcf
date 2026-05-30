"""Translate reference ``vcf_automation`` pillar into native ``saltext.vcf``."""

from __future__ import annotations

from copy import deepcopy


def normalize(pillar: dict) -> dict:
    """Return a native ``saltext.vcf`` pillar fragment.

    Some orchestration layers store topology under ``vcf_automation`` while this
    extension reads connection/config data from ``saltext.vcf``. This helper
    keeps the raw Installer SddcSpec intact and only moves data between those
    two shapes.
    """
    auto = deepcopy((pillar or {}).get("vcf_automation", {}))
    topology = auto.get("topology", {}) or {}
    connections = auto.get("connections", {}) or {}
    installer = topology.get("vcf_installer", {}) or {}

    native = deepcopy((pillar or {}).get("saltext.vcf", {}) or {})
    native.setdefault("vcf_installer", _connection(connections.get("vcf_installer", {})))
    native.setdefault("sddc_manager", _connection(connections.get("sddc_manager", {})))
    native.setdefault("vcenter", _connection(connections.get("vcenter", {})))
    native.setdefault("nsx", _connection(connections.get("nsxt", {})))

    if installer:
        native.setdefault("installer_appliance", _installer_appliance(installer))
        if installer.get("sddc_spec"):
            native.setdefault("bringup_spec", deepcopy(installer["sddc_spec"]))
        if installer.get("timeout_sec") and "bringup_timeout" not in native:
            native["bringup_timeout"] = installer["timeout_sec"]

    for key in ("sddc_manager", "vcenter", "esxi_hosts", "nsxt", "poc_validation"):
        if key in topology:
            native.setdefault(_native_topology_key(key), deepcopy(topology[key]))

    return native


def normalized_pillar(pillar: dict) -> dict:
    """Return *pillar* with ``saltext.vcf`` populated from ``vcf_automation``."""
    result = deepcopy(pillar or {})
    result["saltext.vcf"] = normalize(result)
    return result


def _connection(conn: dict) -> dict:
    return {k: v for k, v in deepcopy(conn or {}).items() if v is not None}


def _installer_appliance(installer: dict) -> dict:
    fields = (
        "installer_host",
        "installer_port",
        "installer_ova_url",
        "installer_deploy_esxi",
        "installer_vm_name",
        "esxi_hosts",
        "network_map",
        "ovf_properties",
        "datastore",
        "disk_provisioning",
        "power_on",
        "verify_ssl",
        "upload_timeout",
        "timeout_sec",
        "polling_interval_sec",
    )
    out = {k: deepcopy(installer[k]) for k in fields if k in installer}
    out.setdefault("deployment_backend", installer.get("deployment_backend", "ovftool"))
    if installer.get("ovftool_path"):
        out["ovftool_path"] = installer["ovftool_path"]
    if installer.get("ovftool_extra_args"):
        out["ovftool_extra_args"] = deepcopy(installer["ovftool_extra_args"])
    return out


def _native_topology_key(key: str) -> str:
    if key == "nsxt":
        return "nsxt_topology"
    if key in ("sddc_manager", "vcenter"):
        return f"{key}_topology"
    return key
