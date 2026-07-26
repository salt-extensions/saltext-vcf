"""State module for SDDC Manager CEIP participation.

CEIP is toggled centrally at SDDC Manager on VCF 9.x; the older
per-vCenter ``/api/appliance/ceip`` REST endpoint returns 404 on VCF 9.1
GA and later. The PATCH is asynchronous -- ``wait`` (default True) makes
the state block until the SDDC task reaches a terminal status so
subsequent states can chain deterministically.
"""

from saltext.vcf.clients import sddc_ceip as c
from saltext.vcf.clients import sddc_tasks

__virtualname__ = "vcf_sddc_ceip"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


# The desired "settled" states -- anything else is either mid-transition or
# a previous run that failed.
_ENABLED_TARGETS = {c.STATE_ENABLED, c.STATE_ENABLING}
_DISABLED_TARGETS = {c.STATE_DISABLED, c.STATE_DISABLING}


def _current(profile=None):
    body = c.get(__opts__, profile=profile) or {}
    return body.get("status")


def _apply(name, desired_enabled, profile=None, wait=True, timeout=3600, poll_interval=10):
    ret = _ret(name)
    current = _current(profile=profile)
    desired_state = c.STATE_ENABLED if desired_enabled else c.STATE_DISABLED

    # Already in the target settled state -> no-op.
    if current == desired_state:
        ret["comment"] = f"CEIP already {desired_state}"
        return ret

    # Already transitioning toward the target -> optionally wait, but no PATCH.
    in_flight_target = c.STATE_ENABLING if desired_enabled else c.STATE_DISABLING
    if current == in_flight_target:
        ret["comment"] = f"CEIP already {current}; leaving in-flight transition alone"
        return ret

    if __opts__.get("test"):
        ret["result"] = None
        ret["comment"] = f"CEIP would change: {current} -> {desired_state}"
        return ret

    task = c.set_(__opts__, desired_enabled, profile=profile) or {}
    task_id = task.get("id")
    ret["changes"] = {"status": {"old": current, "new": desired_state}}

    if wait and task_id:
        try:
            sddc_tasks.wait(
                __opts__, task_id, timeout=timeout, poll_interval=poll_interval, profile=profile
            )
        except (RuntimeError, TimeoutError) as exc:
            ret["result"] = False
            ret["comment"] = f"CEIP task {task_id} did not complete cleanly: {exc}"
            return ret
        final = _current(profile=profile)
        ret["changes"]["status"]["new"] = final
        ret["comment"] = f"CEIP {desired_state.lower()} (task {task_id} -> {final})"
    else:
        ret["comment"] = f"CEIP PATCH submitted (task {task_id or '?'}); state was {current}"

    return ret


def enabled(name, profile=None, wait=True, timeout=3600, poll_interval=10):
    """Ensure CEIP is enabled at SDDC Manager. Async by default; ``wait=True`` blocks."""
    return _apply(
        name,
        desired_enabled=True,
        profile=profile,
        wait=wait,
        timeout=timeout,
        poll_interval=poll_interval,
    )


def disabled(name, profile=None, wait=True, timeout=3600, poll_interval=10):
    """Ensure CEIP is disabled at SDDC Manager (912-controls / STIG opt-out)."""
    return _apply(
        name,
        desired_enabled=False,
        profile=profile,
        wait=wait,
        timeout=timeout,
        poll_interval=poll_interval,
    )
