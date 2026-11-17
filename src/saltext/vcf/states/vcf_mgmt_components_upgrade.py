# pylint: disable=broad-exception-caught
import logging

log = logging.getLogger(__name__)
__virtualname__ = "vcf_mgmt_components_upgrade"


def __virtual__():
    return __virtualname__


def _run(name, func, dry_run_aware, kwargs):
    ret = {"name": name, "result": True, "changes": {}, "comment": ""}
    test = __opts__.get("test", False)
    try:
        if dry_run_aware:
            kwargs["dry_run"] = test
        result = __salt__[f"vcf_mgmt_components_upgrade.{func}"](**kwargs)
    except Exception as exc:
        log.exception("mgmt_components_upgrade state failed")
        ret["result"] = False
        ret["comment"] = str(exc)
        return ret
    ret["result"] = bool(result.get("success", result.get("result", True)))
    ret["comment"] = result.get("comment", "")
    ret["changes"] = result.get("changes", {}) if result.get("changed") else {}
    if result.get("changed") and test:
        ret["result"] = None
    return ret


def ready_validated(name, **kwargs):
    return _run(name, "validate_ready", False, kwargs)


def plan_configured(name, **kwargs):
    return _run(name, "configure_plan", True, kwargs)


def upgrade_applied(name, **kwargs):
    return _run(name, "apply_upgrade", True, kwargs)


def full_upgrade(name, **kwargs):
    return _run(name, "full_upgrade", True, kwargs)


def reported(name, **kwargs):
    return _run(name, "report", False, kwargs)
