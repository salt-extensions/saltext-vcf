# pylint: disable=broad-exception-caught
"""Upgrade the Fleet Lifecycle (``FLEET_LCM``) appliance from VCF Operations.

Pillar section ``fleet_lcm`` supplies ``host`` (the Fleet Lifecycle FQDN from VCF Operations
Build > Lifecycle > VCF Management > Components), ``ops_host`` (the VCF Operations FQDN that
brokers the token exchange), ``username`` / ``password`` (VCF Operations credentials) and
``verify_ssl``.
"""

import logging

from saltext.vcf.clients.fleet_lcm import CommandExecutionError
from saltext.vcf.clients.fleet_lcm import FleetLcmClient
from saltext.vcf.utils.config import as_bool
from saltext.vcf.utils.config import as_int
from saltext.vcf.utils.config import get_section

log = logging.getLogger(__name__)
__virtualname__ = "vcf_fleet_lcm"


def __virtual__():
    return __virtualname__


def _missing(value):
    return not value or str(value).strip() in ("**********", "None", "")


def _client(
    host=None, ops_host=None, username=None, password=None, verify_ssl=None, timeout=None, **_
):
    cfg = get_section(globals().get("__salt__", {}), "fleet_lcm", {})
    host = host or cfg.get("host")
    ops_host = ops_host or cfg.get("ops_host")
    if _missing(host):
        raise CommandExecutionError(
            "Missing fleet_lcm host. Pass host or set the fleet_lcm pillar to the Fleet Lifecycle FQDN."
        )
    if _missing(ops_host):
        raise CommandExecutionError(
            "Missing fleet_lcm ops_host. Pass ops_host or set the fleet_lcm pillar to the VCF Operations FQDN."
        )
    return FleetLcmClient(
        host=host,
        ops_host=ops_host,
        username=username or cfg.get("username") or "admin",
        password=password or cfg.get("password"),
        verify_ssl=as_bool(cfg.get("verify_ssl") if verify_ssl is None else verify_ssl, False),
        timeout=as_int(timeout or cfg.get("timeout"), 300),
        logger=log,
    )


def _result(changed, comment, data=None):
    return {
        "changed": bool(changed),
        "success": True,
        "result": True,
        "comment": comment,
        "data": data or {},
        "changes": data or {} if changed else {},
    }


def get_system_info(**kwargs):
    return _client(**kwargs).get_system()


def validate_ready(target_version=None, **kwargs):
    """Authenticate and confirm an upgrade target is available."""
    client = _client(**kwargs)
    system = client.get_system()
    target = client.select_target_version(system, target_version)
    return _result(
        False,
        f"Fleet Lifecycle is reachable; target version {target} is available",
        {
            "current_version": client.current_version(system),
            "target_version": target,
            "available_versions": client.available_versions(system),
        },
    )


def _plan_or_apply(kind, target_version, timeout_seconds, poll_interval_seconds, dry_run, kwargs):
    client = _client(**kwargs)
    system = client.get_system()
    target = client.select_target_version(system, target_version)
    current = client.current_version(system)
    data = {"current_version": current, "target_version": target}
    if current and str(current) == target:
        return _result(False, f"Fleet Lifecycle is already at {target}", data)
    if as_bool(dry_run, False):
        return _result(True, f"Fleet Lifecycle upgrade {kind} to {target} would be submitted", data)
    submit = client.configure_plan if kind == "plan" else client.apply_upgrade
    task_id = submit(target)
    data["task"] = client.wait_for_task(
        task_id, as_int(timeout_seconds, 7200), as_int(poll_interval_seconds, 15)
    )
    return _result(True, f"Fleet Lifecycle upgrade {kind} for {target} completed", data)


def configure_plan(
    target_version=None, timeout_seconds=7200, poll_interval_seconds=15, dry_run=False, **kwargs
):
    return _plan_or_apply(
        "plan", target_version, timeout_seconds, poll_interval_seconds, dry_run, kwargs
    )


def apply_upgrade(
    target_version=None, timeout_seconds=7200, poll_interval_seconds=15, dry_run=False, **kwargs
):
    return _plan_or_apply(
        "apply", target_version, timeout_seconds, poll_interval_seconds, dry_run, kwargs
    )


def full_upgrade(
    target_version=None, timeout_seconds=7200, poll_interval_seconds=15, dry_run=False, **kwargs
):
    ready = validate_ready(target_version, **kwargs)
    target = ready["data"]["target_version"]
    plan = configure_plan(target, timeout_seconds, poll_interval_seconds, dry_run, **kwargs)
    apply_ = apply_upgrade(target, timeout_seconds, poll_interval_seconds, dry_run, **kwargs)
    return _result(
        plan["changed"] or apply_["changed"],
        f"Fleet Lifecycle full upgrade to {target} completed/submitted",
        {"ready": ready["data"], "plan": plan["data"], "apply": apply_["data"]},
    )


def sync_depot_metadata(timeout_seconds=1800, poll_interval_seconds=15, dry_run=False, **kwargs):
    """Sync the software depot metadata (VCF Operations Build > Lifecycle) and wait for the task."""
    client = _client(**kwargs)
    if as_bool(dry_run, False):
        return _result(True, "Software depot metadata sync would be submitted")
    task_id = client.sync_depot_metadata()
    task = client.wait_for_task(
        task_id, as_int(timeout_seconds, 1800), as_int(poll_interval_seconds, 15)
    )
    return _result(True, "Software depot metadata synced", {"task": task})


def report(**kwargs):
    return _result(False, "Fleet Lifecycle status collected", {"system": get_system_info(**kwargs)})
