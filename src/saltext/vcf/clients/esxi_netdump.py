"""ESXi network coredump ("netdump") via ``esxcli`` over SSH.

Network coredump has never had a vim25 ``HostSystem.configManager`` manager
the way NTP/DNS/syslog/firewall do -- the only APIs are ``esxcli system
coredump network`` and the equivalent vSphere Automation "ESXCLI over SOAP"
bridge (``vim.EsxCLI`` via ``ReflectManagedMethodExecuter``), which is a much
more fragile, poorly-documented mechanism. Since this host already has an SSH
helper for appliance-local controls (:mod:`saltext.vcf.utils.ssh`), running
the plain ``esxcli`` command directly is the more robust choice.
"""

from saltext.vcf.utils import esxi
from saltext.vcf.utils import ssh as ssh_util

_GET_CMD = "esxcli system coredump network get"


def _parse_get_output(text):
    """Parse ``esxcli system coredump network get`` key/value output."""
    values = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        values[key.strip()] = value.strip()
    return {
        "enabled": values.get("Enabled", "").lower() == "true",
        "interface_name": values.get("Host VNic") or None,
        "server_ip": values.get("Network Server IP") or None,
        "server_port": (
            int(values["Network Server Port"]) if values.get("Network Server Port") else None
        ),
    }


def get(opts, profile=None):
    """Return the current network coredump config."""
    ssh_cfg = esxi.get_ssh_config(opts, profile=profile)
    rc, out, err = ssh_util.run(ssh_cfg, _GET_CMD)
    if rc != 0:
        raise RuntimeError(
            f"esxcli system coredump network get failed on {ssh_cfg.get('host')}: {err.strip()}"
        )
    return _parse_get_output(out)


def set_network(opts, interface_name, server_ip, server_port, profile=None):
    """Configure the netdump collector target. Does not itself enable collection."""
    ssh_cfg = esxi.get_ssh_config(opts, profile=profile)
    cmd = (
        "esxcli system coredump network set "
        f"--interface-name={interface_name} --server-ip={server_ip} --server-port={server_port}"
    )
    rc, _out, err = ssh_util.run(ssh_cfg, cmd)
    if rc != 0:
        raise RuntimeError(
            f"esxcli system coredump network set failed on {ssh_cfg.get('host')}: {err.strip()}"
        )


def set_enabled(opts, enabled, profile=None):
    """Enable or disable network coredump collection."""
    ssh_cfg = esxi.get_ssh_config(opts, profile=profile)
    value = "true" if enabled else "false"
    rc, _out, err = ssh_util.run(ssh_cfg, f"esxcli system coredump network set --enable={value}")
    if rc != 0:
        raise RuntimeError(
            f"esxcli system coredump network set --enable failed on {ssh_cfg.get('host')}: {err.strip()}"
        )
