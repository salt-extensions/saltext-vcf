"""Resource layer for VMSP syslog configuration (``vsp`` component logs spec)."""

from saltext.vcf.utils import vmsp


def _component(opts, profile=None):
    component = vmsp.get_component(opts, profile=profile)
    if component is None:
        raise ValueError(f"VMSP component '{vmsp.VSP_COMPONENT_NAME}' not found")
    return component


def get(opts, profile=None):
    """Return current syslog config as ``{"syslog": {...}}``."""
    component = _component(opts, profile=profile)
    logs = component.get("spec", {}).get("configuration", {}).get("logs", {})
    return {"syslog": logs.get("syslog", {})}


def set_(opts, host, port=514, transport="tcp", insecure=False, cacert=None, profile=None):
    """Apply the desired syslog server settings to the ``vsp`` component."""
    component = _component(opts, profile=profile)
    syslog = {
        "host": host,
        "port": port,
        "insecure": insecure,
        "transport": transport,
    }
    if cacert:
        syslog["cacert"] = cacert
    payload = {"spec": {"configuration": {"logs": {"syslog": syslog}}}}
    task_id = vmsp.apply_component(opts, component["id"], payload, profile=profile)
    return vmsp.wait_for_task(opts, task_id, profile=profile)
