"""Declarative VCF upgrades with Salt test-mode semantics and persistent resume."""

import logging

from saltext.vcf.utils.vcf_upgrade_transport import boolean

log = logging.getLogger(__name__)
__virtualname__ = "vcf_upgrade"


def __virtual__():
    return __virtualname__


def _call(name, function, **kwargs):
    ret = {"name": name, "result": True, "changes": {}, "comment": ""}
    try:
        # Salt's global test flag takes precedence over any caller-supplied dry_run.
        requested = kwargs.pop("dry_run", False)
        dry_run = boolean(__opts__.get("test", False)) or boolean(requested)
        data = __salt__[function](dry_run=dry_run, **kwargs)
        ret["comment"] = data["comment"]
        if data.get("changed"):
            ret["changes"] = data.get("data", {})
            ret["result"] = None if dry_run else True
    except Exception as exc:  # Salt states return execution failures to the state engine.
        log.debug("VCF upgrade state failed (%s)", type(exc).__name__)
        ret["result"] = False
        ret["comment"] = str(exc)
    return ret


def bundle_downloaded(name, **kwargs):
    """Ensure a component bundle is downloaded."""
    return _call(name, "vcf_upgrade.download_bundle", **kwargs)


def upgrade_created(name, **kwargs):
    """Ensure a checkpointed upgrade exists; SDDC Manager creation can self-start."""
    return _call(name, "vcf_upgrade.create_upgrade", **kwargs)


def upgrade_executed(name, upgrade_id, **kwargs):
    """Explicitly execute an existing draft; prefer upgraded for automatic prechecks."""
    return _call(name, "vcf_upgrade.execute_upgrade", upgrade_id=upgrade_id, **kwargs)


def upgrade_monitored(name, upgrade_id, **kwargs):
    """Monitor without reporting a configuration change or blocking test mode."""
    ret = {"name": name, "result": True, "changes": {}, "comment": ""}
    if __opts__.get("test", False):
        ret.update(result=None, comment="Would monitor VCF upgrade completion")
        return ret
    try:
        data = __salt__["vcf_upgrade.wait_for_upgrade"](upgrade_id=upgrade_id, **kwargs)
        ret["comment"] = data["comment"]
    except Exception as exc:
        ret.update(result=False, comment=str(exc))
    return ret


def upgraded(name, **kwargs):
    """Run/resume a single component with prechecks and inventory verification."""
    return _call(name, "vcf_upgrade.run", **kwargs)


def sequence_completed(name, **kwargs):
    """Run/resume an explicit component sequence."""
    return _call(name, "vcf_upgrade.run_sequence", **kwargs)
