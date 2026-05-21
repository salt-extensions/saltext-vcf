"""State module: ensure the VCF Installer appliance is deployed and reachable."""

import logging

from saltext.vcf.modules import vcf_installer_appliance as m

log = logging.getLogger(__name__)

__virtualname__ = "vcf_installer_appliance"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def running(name, installer_spec=None):
    """Ensure the VCF Installer appliance referenced by *installer_spec* is up.

    Idempotent: if the appliance HTTPS port is already accepting TCP
    connections, the state is a no-op. Otherwise the OVA is deployed via
    :mod:`saltext.vcf.modules.vcf_installer_appliance` and the state
    waits for the appliance to become reachable.

    *installer_spec* defaults to pillar ``saltext.vcf:installer_appliance``.
    """
    ret = _ret(name)
    spec = m._resolve_spec(installer_spec)  # noqa: SLF001
    host = spec["installer_host"]
    port = int(spec.get("installer_port", 443))

    if m.is_reachable(host, port=port):
        ret["comment"] = f"{host}:{port} already reachable"
        return ret

    if __opts__.get("test"):  # noqa: F821
        ret["result"] = None
        ret["comment"] = f"would deploy installer OVA to {spec.get('installer_deploy_esxi')!r}"
        ret["changes"] = {"plan": "deploy_installer_ova", "target_host": host}
        return ret

    try:
        result = m.ensure_running(spec)
    except (RuntimeError, TimeoutError, LookupError, FileNotFoundError) as exc:
        ret["result"] = False
        ret["comment"] = f"installer deploy failed: {exc}"
        return ret

    ret["changes"] = {
        "deployed": result.get("deployed", False),
        "vm_name": result.get("vm_name"),
        "vm_moid": result.get("vm_moid"),
        "powered_on": result.get("powered_on"),
        "elapsed_sec": result.get("elapsed_sec"),
    }
    ret["comment"] = f"installer appliance reachable at {host}:{port}"
    return ret
