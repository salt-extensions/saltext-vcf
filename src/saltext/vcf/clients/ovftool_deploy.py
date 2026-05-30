"""Deploy an OVA by shelling out to VMware ``ovftool``.

This backend is intentionally separate from :mod:`saltext.vcf.clients.ovf_deploy`.
The pyVmomi backend uses ``ResourcePool.ImportVApp`` directly, which can be
blocked by standalone ESXi licensing. ``ovftool`` uses VMware's supported CLI
path and has been validated against standalone ESXi targets when thin
provisioning is requested.
"""

import logging
import shutil
import subprocess
import time
from urllib.parse import quote

log = logging.getLogger(__name__)


def deploy_ova(
    *,
    ova_source,
    target_host,
    target_user,
    target_password,
    target_port=443,
    vm_name,
    datastore=None,
    network_map=None,
    ovf_properties=None,
    disk_provisioning="thin",
    deployment_option=None,
    power_on=True,
    verify_ssl=False,
    upload_timeout=7200,
    ovftool_path="ovftool",
    extra_args=None,
):
    """Deploy an OVA to *target_host* using the external ``ovftool`` binary.

    The argument shape mirrors :func:`saltext.vcf.clients.ovf_deploy.deploy_ova`
    so callers can switch backends without changing pillar structure. Returns a
    dict containing the VM name, power-on intent, elapsed seconds, and captured
    command output.
    """
    start = time.monotonic()
    cmd = _build_command(
        ova_source=ova_source,
        target_host=target_host,
        target_user=target_user,
        target_password=target_password,
        target_port=target_port,
        vm_name=vm_name,
        datastore=datastore,
        network_map=network_map,
        ovf_properties=ovf_properties,
        disk_provisioning=disk_provisioning,
        deployment_option=deployment_option,
        power_on=power_on,
        verify_ssl=verify_ssl,
        ovftool_path=_resolve_ovftool(ovftool_path),
        extra_args=extra_args,
    )
    log.info("Deploying OVA %s to %s with ovftool", ova_source, target_host)
    proc = subprocess.run(  # noqa: S603
        cmd,
        capture_output=True,
        text=True,
        check=False,
        timeout=float(upload_timeout),
    )
    elapsed = round(time.monotonic() - start, 2)
    if proc.returncode != 0:
        raise RuntimeError(
            "ovftool deployment failed "
            f"(exit {proc.returncode}) stdout={proc.stdout!r} stderr={proc.stderr!r}"
        )
    return {
        "vm_name": vm_name,
        "vm_moid": None,
        "powered_on": bool(power_on),
        "elapsed_sec": elapsed,
        "backend": "ovftool",
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def _resolve_ovftool(ovftool_path):
    if "/" in ovftool_path:
        return ovftool_path
    resolved = shutil.which(ovftool_path)
    if not resolved:
        raise FileNotFoundError(f"ovftool binary {ovftool_path!r} not found on PATH")
    return resolved


def _build_command(
    *,
    ova_source,
    target_host,
    target_user,
    target_password,
    target_port,
    vm_name,
    datastore,
    network_map,
    ovf_properties,
    disk_provisioning,
    deployment_option,
    power_on,
    verify_ssl,
    ovftool_path,
    extra_args,
):
    cmd = [ovftool_path, "--acceptAllEulas"]
    if not verify_ssl:
        cmd.append("--noSSLVerify")
    if datastore:
        cmd.append(f"--datastore={datastore}")
    if disk_provisioning:
        cmd.append(f"--diskMode={disk_provisioning}")
    if deployment_option:
        cmd.append(f"--deploymentOption={deployment_option}")
    if vm_name:
        cmd.append(f"--name={vm_name}")
    if power_on:
        cmd.append("--powerOn")
    for ovf_net, target_net in (network_map or {}).items():
        cmd.append(f"--net:{ovf_net}={target_net}")
    for key, value in (ovf_properties or {}).items():
        cmd.append(f"--prop:{key}={value}")
    cmd.extend(extra_args or [])
    cmd.extend([ova_source, _target_url(target_host, target_user, target_password, target_port)])
    return cmd


def _target_url(host, user, password, port):
    auth = f"{quote(str(user), safe='')}:{quote(str(password), safe='')}"
    port_part = "" if int(port) == 443 else f":{int(port)}"
    return f"vi://{auth}@{host}{port_part}/"
