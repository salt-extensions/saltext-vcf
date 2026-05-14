"""State module for VCF Installer bringup."""

import logging

from saltext.vmware.clients import installer_bringup as c

log = logging.getLogger(__name__)

__virtualname__ = "vmware_installer_bringup"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def _find_active_sddc(opts, profile=None):
    """Return the most recent bringup task, or None."""
    try:
        tasks = c.list_(opts, profile=profile)
    except Exception:  # pylint: disable=broad-except
        return None
    if not tasks:
        return None
    # Latest by id (monotonic) or by status: we just take the first IN_PROGRESS
    # or the most recently completed.
    for t in tasks:
        if t.get("status") in ("IN_PROGRESS", "PENDING", "QUEUED"):
            return t
    return tasks[0]


def validated(name, spec, wait=True, timeout=1800, profile=None):
    """Ensure *spec* passes installer validation.

    Submits a validation, optionally waits for it, and reports success/failure.
    """
    ret = _ret(name)
    val = c.validate(__opts__, spec, profile=profile)
    val_id = val.get("id")
    ret["changes"] = {"validation_id": val_id}
    if not wait:
        ret["comment"] = f"validation {val_id} submitted"
        return ret
    if __opts__.get("test"):
        ret["result"] = None
        ret["comment"] = f"would wait for validation {val_id}"
        return ret
    try:
        final = c.wait_validation(__opts__, val_id, timeout=timeout, profile=profile)
    except (TimeoutError, RuntimeError) as exc:
        ret["result"] = False
        ret["comment"] = f"validation {val_id} failed: {exc}"
        return ret
    ret["comment"] = f"validation {val_id} succeeded: {final.get('resultStatus')}"
    return ret


def complete(  # pylint: disable=too-many-return-statements
    name, spec, wait=True, timeout=14400, validate_first=True, profile=None
):
    """Ensure a management-domain bringup has completed.

    Idempotent based on the installer's task list: if an in-progress or
    completed bringup is present, this state reuses it instead of submitting a
    new one. *validate_first* runs validation before submitting.
    """
    ret = _ret(name)
    existing = _find_active_sddc(__opts__, profile=profile)
    if existing is not None:
        state = existing.get("status")
        if state in ("COMPLETED_WITH_SUCCESS", "SUCCEEDED", "COMPLETED"):
            ret["comment"] = f"bringup {existing.get('id')} already complete"
            return ret
        if state in ("IN_PROGRESS", "PENDING", "QUEUED"):
            if __opts__.get("test"):
                ret["result"] = None
                ret["comment"] = f"bringup {existing.get('id')} in progress; would wait"
                return ret
            if not wait:
                ret["comment"] = f"bringup {existing.get('id')} in progress"
                return ret
            try:
                final = c.wait(__opts__, existing.get("id"), timeout=timeout, profile=profile)
            except (TimeoutError, RuntimeError) as exc:
                ret["result"] = False
                ret["comment"] = f"bringup {existing.get('id')} failed: {exc}"
                return ret
            ret["changes"] = {"sddc_id": existing.get("id"), "status": final.get("status")}
            ret["comment"] = "bringup completed"
            return ret
        # Failed previous bringup — let the user decide (don't auto-retry).
        ret["result"] = False
        ret["comment"] = (
            f"prior bringup {existing.get('id')} ended {state!r}; manual retry required"
        )
        return ret

    if __opts__.get("test"):
        ret["result"] = None
        ret["comment"] = "would validate and submit bringup"
        return ret

    if validate_first:
        v_result = validated(f"{name}/validate", spec, wait=True, timeout=1800, profile=profile)
        if not v_result.get("result"):
            return v_result

    submitted = c.submit(__opts__, spec, profile=profile)
    sddc_id = submitted.get("id")
    ret["changes"]["sddc_id"] = sddc_id
    if not wait:
        ret["comment"] = f"bringup {sddc_id} submitted"
        return ret
    try:
        final = c.wait(__opts__, sddc_id, timeout=timeout, profile=profile)
    except (TimeoutError, RuntimeError) as exc:
        ret["result"] = False
        ret["comment"] = f"bringup {sddc_id} failed: {exc}"
        return ret
    ret["changes"]["status"] = final.get("status")
    ret["comment"] = f"bringup {sddc_id} completed"
    return ret
