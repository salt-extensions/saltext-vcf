"""Resource layer for VMSP DNS configuration (``vsp`` component network spec)."""

from saltext.vcf.utils import vmsp


def _component(opts, profile=None):
    component = vmsp.get_component(opts, profile=profile)
    if component is None:
        raise ValueError(f"VMSP component '{vmsp.VSP_COMPONENT_NAME}' not found")
    return component


def get(opts, profile=None):
    """Return current DNS config as ``{"servers": [...]}``."""
    component = _component(opts, profile=profile)
    network = component.get("spec", {}).get("configuration", {}).get("network", {})
    return {"servers": network.get("dnsServers", [])}


def set_(opts, servers, profile=None):
    """Apply the desired DNS *servers* list to the ``vsp`` component."""
    component = _component(opts, profile=profile)
    payload = {"spec": {"configuration": {"network": {"dnsServers": list(servers)}}}}
    task_id = vmsp.apply_component(opts, component["id"], payload, profile=profile)
    return vmsp.wait_for_task(opts, task_id, profile=profile)
