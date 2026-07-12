"""State module for ESXi services (running/stopped + startup policy)."""

from saltext.vcf.clients import esxi_service as c

__virtualname__ = "vcf_esxi_service"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def _get_or_fail(name, profile):
    svc = c.get_or_none(__opts__, name, profile=profile)
    if svc is None:
        return None, f"Service {name} does not exist on this host"
    return svc, None


def running(name, policy=None, profile=None):  # pylint: disable=redefined-outer-name
    """Ensure service *name* is running. Optionally pin its startup *policy*."""
    ret = _ret(name)
    svc, err = _get_or_fail(name, profile)
    if err:
        ret["result"] = False
        ret["comment"] = err
        return ret

    actions = []
    changes = {}
    if not c.is_running(svc):
        actions.append("start")
        changes["state"] = {"old": svc.get("state"), "new": "RUNNING"}
    if policy is not None and svc.get("policy") != policy:
        actions.append(f"policy={policy}")
        changes["policy"] = {
            "old": svc.get("policy"),
            "new": policy,
        }

    if not actions:
        ret["comment"] = f"Service {name} already running" + (
            f" with policy {policy}" if policy else ""
        )
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Service {name} would be updated: {', '.join(actions)}"
        return ret
    if "start" in actions:
        c.start(__opts__, name, profile=profile)
    if policy is not None and svc.get("policy") != policy:
        c.set_policy(__opts__, name, policy, profile=profile)
    ret["changes"] = changes
    ret["comment"] = f"Service {name}: {', '.join(actions)}"
    return ret


def stopped(name, policy=None, profile=None):  # pylint: disable=redefined-outer-name
    """Ensure service *name* is stopped."""
    ret = _ret(name)
    svc, err = _get_or_fail(name, profile)
    if err:
        ret["result"] = False
        ret["comment"] = err
        return ret

    actions = []
    changes = {}
    if c.is_running(svc):
        actions.append("stop")
        changes["state"] = {"old": svc.get("state"), "new": "STOPPED"}
    if policy is not None and svc.get("policy") != policy:
        actions.append(f"policy={policy}")
        changes["policy"] = {
            "old": svc.get("policy"),
            "new": policy,
        }

    if not actions:
        ret["comment"] = f"Service {name} already stopped"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Service {name} would be updated: {', '.join(actions)}"
        return ret
    if "stop" in actions:
        c.stop(__opts__, name, profile=profile)
    if policy is not None and svc.get("policy") != policy:
        c.set_policy(__opts__, name, policy, profile=profile)
    ret["changes"] = changes
    ret["comment"] = f"Service {name}: {', '.join(actions)}"
    return ret


def policy(name, policy, profile=None):  # pylint: disable=redefined-outer-name
    """Ensure service *name*'s startup policy matches *policy* (without touching running state)."""
    ret = _ret(name)
    svc, err = _get_or_fail(name, profile)
    if err:
        ret["result"] = False
        ret["comment"] = err
        return ret
    current = svc.get("policy")
    if current == policy:
        ret["comment"] = f"Service {name} policy already {policy}"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Service {name} policy would change to {policy}"
        return ret
    c.set_policy(__opts__, name, policy, profile=profile)
    ret["changes"] = {"policy": {"old": current, "new": policy}}
    ret["comment"] = f"Service {name} policy set to {policy}"
    return ret
