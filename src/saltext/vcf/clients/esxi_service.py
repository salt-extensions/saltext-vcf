"""ESXi services (TSM-SSH, ntpd, etc.) via SOAP/pyVmomi."""

from saltext.vcf.utils import esxi

# Valid startup policies (uppercase for public API parity with the old REST surface)
POLICIES = ("ON", "OFF", "AUTOMATIC")

# REST → SOAP policy string mapping
_POLICY_TO_SOAP = {"ON": "on", "OFF": "off", "AUTOMATIC": "automatic"}
_POLICY_FROM_SOAP = {"on": "ON", "off": "OFF", "automatic": "AUTOMATIC"}


def _svc_to_dict(svc):
    return {
        "key": svc.key,
        "label": svc.label,
        "running": svc.running,
        "policy": _POLICY_FROM_SOAP.get(svc.policy, svc.policy.upper()),
        "state": "RUNNING" if svc.running else "STOPPED",
    }


def _find_service(svc_system, service):
    for svc in svc_system.serviceInfo.service:
        if svc.key == service:
            return svc
    raise KeyError(f"Service {service!r} not found on this host")


def list_(opts, profile=None):
    host = esxi.get_host_system(opts, profile=profile)
    return {
        svc.key: _svc_to_dict(svc) for svc in host.configManager.serviceSystem.serviceInfo.service
    }


def get(opts, service, profile=None):
    host = esxi.get_host_system(opts, profile=profile)
    svc = _find_service(host.configManager.serviceSystem, service)
    return _svc_to_dict(svc)


def get_or_none(opts, service, profile=None):
    try:
        return get(opts, service, profile=profile)
    except KeyError:
        return None


def start(opts, service, profile=None):
    host = esxi.get_host_system(opts, profile=profile)
    host.configManager.serviceSystem.Start(id=service)
    return get(opts, service, profile=profile)


def stop(opts, service, profile=None):
    host = esxi.get_host_system(opts, profile=profile)
    host.configManager.serviceSystem.Stop(id=service)
    return get(opts, service, profile=profile)


def restart(opts, service, profile=None):
    host = esxi.get_host_system(opts, profile=profile)
    host.configManager.serviceSystem.Restart(id=service)
    return get(opts, service, profile=profile)


def set_policy(opts, service, policy, profile=None):
    """Set startup policy. *policy* in :data:`POLICIES`."""
    if policy not in POLICIES:
        raise ValueError(f"policy must be one of {POLICIES}, got {policy!r}")
    host = esxi.get_host_system(opts, profile=profile)
    host.configManager.serviceSystem.UpdatePolicy(id=service, policy=_POLICY_TO_SOAP[policy])
    return get(opts, service, profile=profile)


def is_running(service_obj):
    """True when a service dict (from :func:`get`) reports running state."""
    return service_obj.get("state") == "RUNNING" or bool(service_obj.get("running"))
