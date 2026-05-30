"""State module for vCenter VM PoC validation."""

from saltext.vcf.clients import vcenter_vm as r

__virtualname__ = "vcf_vcenter_vm"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def deployed(name, spec, profile=None):
    """Ensure a VM exists for validation."""
    ret = _ret(name)
    current = r.get_by_name(__opts__, name, profile=profile)  # noqa: F821
    if current is not None:
        ret["comment"] = f"VM {name} is already present"
        return ret
    if __opts__["test"]:  # noqa: F821
        ret["result"] = None
        ret["comment"] = f"VM {name} would be deployed"
        return ret
    result = r.deploy(__opts__, name, spec, profile=profile)  # noqa: F821
    ret["changes"] = {"deployed": name, **result}
    ret["comment"] = f"VM {name} deployment submitted"
    return ret


def reachable(name, target_ip, port=22, timeout_sec=120, interval_sec=10, profile=None):
    """Ensure a VM target IP is reachable over TCP."""
    ret = _ret(name)
    if __opts__["test"]:  # noqa: F821
        ret["result"] = None
        ret["comment"] = f"would wait for {target_ip}:{port}"
        return ret
    if r.wait_reachable(target_ip, port=port, timeout=timeout_sec, interval=interval_sec):
        ret["comment"] = f"{target_ip}:{port} is reachable"
        return ret
    ret["result"] = False
    ret["comment"] = f"{target_ip}:{port} was not reachable within {timeout_sec}s"
    return ret
