"""VCF Installer appliance bootstrap: deploy the OVA to a bare ESXi host.

The VCF Installer is the OVA you push onto a fresh ESXi host before any
vCenter/SDDC Manager exists. Once it boots, the standard bringup REST
flow (validate + submit) lives in :mod:`saltext.vcf.clients.installer_bringup`.

This module wraps the OVA deployment backends with a pillar-friendly spec shape
and adds TCP reachability helpers used to confirm the appliance has booted.
"""

import logging
import socket
import time

from saltext.vcf.clients import ovf_deploy
from saltext.vcf.clients import ovftool_deploy

log = logging.getLogger(__name__)


def is_appliance_reachable(host, *, port=443, timeout=5):
    """Return ``True`` if a TCP connection to ``(host, port)`` opens.

    TCP-only — the appliance's HTTPS endpoint may still be returning 503s
    while the bringup is in the early boot; what we care about here is
    "the network listener is up".
    """
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def wait_until_reachable(host, *, port=443, timeout=900, poll_interval=15):
    """Block until :func:`is_appliance_reachable` succeeds.

    Raises ``TimeoutError`` after *timeout* seconds.
    """
    deadline = time.monotonic() + float(timeout)
    while True:
        if is_appliance_reachable(host, port=port, timeout=min(5, poll_interval)):
            return
        if time.monotonic() >= deadline:
            raise TimeoutError(f"{host}:{port} not reachable within {timeout}s")
        time.sleep(float(poll_interval))


def deploy_installer(installer_spec):
    """Deploy the VCF Installer OVA per *installer_spec*.

    Required keys:

    - ``installer_ova_url`` — local path or ``http(s)://`` URL to the OVA.
    - ``installer_vm_name`` — name to give the VM on the target host.
    - ``installer_deploy_esxi`` — FQDN/IP of the bare ESXi host.
    - ``esxi_hosts`` — list of ``{fqdn, username, password}`` dicts; the
      entry whose ``fqdn`` matches ``installer_deploy_esxi`` provides the
      ESXi root credentials.

    Optional: ``deployment_backend`` (``pyvmomi`` by default, or
    ``ovftool``), ``datastore``, ``network_map``, ``ovf_properties``,
    ``disk_provisioning``, ``deployment_option``, ``installer_port``
    (default 443), ``power_on`` (default ``True``), ``ovftool_path``,
    and ``ovftool_extra_args``.

    Returns the dict produced by the selected deployment backend.
    """
    target_host = installer_spec["installer_deploy_esxi"]
    creds = _esxi_credentials(installer_spec, target_host)
    backend = installer_spec.get("deployment_backend", "pyvmomi").lower()
    deploy = _deployment_backend(backend)
    kwargs = dict(
        ova_source=installer_spec["installer_ova_url"],
        target_host=target_host,
        target_user=creds["username"],
        target_password=creds["password"],
        target_port=int(installer_spec.get("installer_port", 443)),
        vm_name=installer_spec["installer_vm_name"],
        datastore=installer_spec.get("datastore"),
        network_map=installer_spec.get("network_map"),
        ovf_properties=installer_spec.get("ovf_properties"),
        disk_provisioning=installer_spec.get("disk_provisioning", "thin"),
        deployment_option=installer_spec.get("deployment_option"),
        power_on=installer_spec.get("power_on", True),
        verify_ssl=installer_spec.get("verify_ssl", False),
        upload_timeout=installer_spec.get("upload_timeout", 3600),
    )
    if backend == "ovftool":
        kwargs["ovftool_path"] = installer_spec.get("ovftool_path") or "ovftool"
        kwargs["extra_args"] = installer_spec.get("ovftool_extra_args")
    return deploy(**kwargs)


def _deployment_backend(name):
    if name == "pyvmomi":
        return ovf_deploy.deploy_ova
    if name == "ovftool":
        return ovftool_deploy.deploy_ova
    raise ValueError(f"unsupported installer appliance deployment_backend={name!r}")


def _esxi_credentials(spec, host):
    for entry in spec.get("esxi_hosts") or []:
        if entry.get("fqdn") == host or entry.get("ip") == host:
            return {
                "username": entry.get("username", "root"),
                "password": entry["password"],
            }
    raise LookupError(
        f"no esxi_hosts entry matches installer_deploy_esxi={host!r}; "
        f"available: {[e.get('fqdn') for e in spec.get('esxi_hosts') or []]}"
    )
