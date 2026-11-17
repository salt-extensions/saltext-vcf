# pylint: disable=broad-exception-caught,consider-using-f-string
"""Upgrade the VCF management components from VCF Operations.

Pillar section ``fleet_lcm`` (shared with ``vcf_fleet_lcm``) supplies ``host`` (the Fleet Lifecycle
FQDN from VCF Operations Build > Lifecycle > VCF Management > Upgrade), ``ops_host`` (the VCF
Operations FQDN that brokers the token exchange), ``username`` / ``password`` (VCF Operations
credentials) and ``verify_ssl``.
"""

import logging

from saltext.vcf.clients.fleet_lcm import CommandExecutionError
from saltext.vcf.clients.mgmt_components_upgrade import BLOCKING_STATUSES
from saltext.vcf.clients.mgmt_components_upgrade import SKIP_STATUSES
from saltext.vcf.clients.mgmt_components_upgrade import UPGRADE_ORDER
from saltext.vcf.clients.mgmt_components_upgrade import MgmtComponentsUpgradeClient
from saltext.vcf.clients.mgmt_components_upgrade import release_version
from saltext.vcf.utils.config import as_bool
from saltext.vcf.utils.config import as_int
from saltext.vcf.utils.config import get_section

log = logging.getLogger(__name__)
__virtualname__ = "vcf_mgmt_components_upgrade"


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
    return MgmtComponentsUpgradeClient(
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


def _order(order):
    """``order`` is a list of componentType names; labels default to the type name."""
    if not order:
        return None
    types = order.replace(",", " ").split() if isinstance(order, str) else order
    labels = dict(UPGRADE_ORDER)
    return [(str(t), labels.get(str(t), str(t))) for t in types]


def _order_from_pillar(order):
    if order:
        return order
    return get_section(globals().get("__salt__", {}), "fleet_lcm", {}).get("upgrade_order")


def _context(client, target_version, order=None, plan_id=None):
    """Resolve plan, release, desired state and the ordered component queue."""
    release = client.select_release(client.list_releases(), target_version)
    plan, plan_warnings = client.select_plan(client.list_plans(), plan_id)
    desired = client.desired_state(release)
    queue, warnings = client.build_queue(
        client.list_components(), release, _order(_order_from_pillar(order))
    )
    plan_components = client.get_plan_components(plan["id"])
    for comp in queue:
        in_plan = plan_components.get(comp["id"])
        comp["status"] = in_plan.get("status") if in_plan else None
        comp["depends_on"] = (in_plan or {}).get("dependsOn") or []
        if not in_plan:
            warnings.append(
                f"{comp['label']} is not in upgrade plan {plan['id']}; readiness unknown."
            )
    return {
        "plan_id": plan["id"],
        "target_version": release_version(release),
        "desired_state": desired,
        "plan_up_to_date": client.plan_matches(plan, desired),
        "queue": queue,
        "warnings": plan_warnings + warnings,
    }


def validate_ready(target_version=None, order=None, plan_id=None, **kwargs):
    """Authenticate and confirm a plan, a target release and the ordered component queue exist."""
    ctx = _context(_client(**kwargs), target_version, order, plan_id)
    for warning in ctx["warnings"]:
        log.warning(warning)
    return _result(
        False,
        "VCF management components upgrade to {} is available; order: {}".format(
            ctx["target_version"], " -> ".join(c["label"] for c in ctx["queue"])
        ),
        ctx,
    )


def configure_plan(
    target_version=None,
    order=None,
    plan_id=None,
    timeout_seconds=3600,
    poll_interval_seconds=15,
    dry_run=False,
    **kwargs,
):
    """Patch the active upgrade plan with the desired software of the target release."""
    client = _client(**kwargs)
    ctx = _context(client, target_version, order, plan_id)
    target = ctx["target_version"]
    if ctx["plan_up_to_date"]:
        return _result(False, f"Upgrade plan {ctx['plan_id']} already targets {target}", ctx)
    if as_bool(dry_run, False):
        return _result(True, f"VCF management components plan for {target} would be submitted", ctx)
    timeout, poll = as_int(timeout_seconds, 3600), as_int(poll_interval_seconds, 15)
    task_id = client.set_desired_state(ctx["plan_id"], ctx["desired_state"])
    if task_id:
        ctx["task"] = client.wait_for_task(task_id, timeout, poll)
    ctx["plan"] = client.wait_for_plan_ready(ctx["plan_id"], ctx["desired_state"], timeout, poll)
    return _result(True, f"VCF management components plan for {target} configured", ctx)


def apply_upgrade(
    target_version=None,
    order=None,
    plan_id=None,
    timeout_seconds=7200,
    poll_interval_seconds=15,
    dry_run=False,
    **kwargs,
):
    """Upgrade the components one at a time in the mandatory order: precheck, apply, wait.

    The first failure raises, so later components are never upgraded on top of a failed one.
    Components already at the desired version are skipped.
    """
    client = _client(**kwargs)
    ctx = _context(client, target_version, order, plan_id)
    target = ctx["target_version"]
    pending = [
        c
        for c in ctx["queue"]
        if c.get("status") not in SKIP_STATUSES
        and not (c["current"] and str(c["current"]) == str(c["desired"]))
    ]
    ctx["pending"] = [c["label"] for c in pending]
    if not pending:
        return _result(False, f"All management components are already at {target}", ctx)
    if as_bool(dry_run, False):
        return _result(
            True,
            "VCF management components upgrade to {} would run in order: {}".format(
                target, " -> ".join(c["label"] for c in pending)
            ),
            ctx,
        )
    timeout, poll = as_int(timeout_seconds, 7200), as_int(poll_interval_seconds, 15)
    busy = client.running_workflows()
    if busy:
        raise CommandExecutionError(
            "Upgrade tasks are already running ({}); not starting another. Wait for them to finish.".format(
                ", ".join(f"{t.get('resourceType')} {t.get('type')}" for t in busy)
            )
        )
    ctx["results"] = []
    for comp in pending:
        # Re-check live: the previous upgrade changes this component's readiness.
        live = client.get_plan_components(ctx["plan_id"], comp["id"]).get(comp["id"])
        if live and live.get("status") in SKIP_STATUSES:
            log.info("%s is %s; skipping", comp["label"], live["status"])
            ctx["results"].append({"component": comp["label"], "skipped": live["status"]})
            continue
        if live and live.get("status") in BLOCKING_STATUSES:
            raise CommandExecutionError(
                "{} is not ready to upgrade ({}); not continuing, so later components stay untouched.".format(
                    comp["label"], client.component_problem(live)
                )
            )
        log.info("Upgrading %s %s to %s", comp["label"], comp["fqdn"], comp["desired"])
        pre_task = client.precheck(ctx["plan_id"], comp["id"])
        client.assert_scope(pre_task, comp["id"])
        pre = client.wait_for_task(pre_task, timeout, poll)
        done = client.wait_for_task(client.apply(ctx["plan_id"], comp["id"]), timeout, poll)
        ctx["results"].append(
            {"component": comp["label"], "precheck": pre["status"], "apply": done["status"]}
        )
    return _result(True, f"VCF management components upgrade to {target} completed", ctx)


def full_upgrade(
    target_version=None,
    order=None,
    plan_id=None,
    plan_timeout_seconds=3600,
    apply_timeout_seconds=7200,
    poll_interval_seconds=15,
    dry_run=False,
    **kwargs,
):
    """Validate, configure the plan, then upgrade every component in order."""
    ready = validate_ready(target_version, order, plan_id, **kwargs)
    target = ready["data"]["target_version"]
    steps = {
        "plan": configure_plan(
            target, order, plan_id, plan_timeout_seconds, poll_interval_seconds, dry_run, **kwargs
        ),
        "apply": apply_upgrade(
            target, order, plan_id, apply_timeout_seconds, poll_interval_seconds, dry_run, **kwargs
        ),
    }
    return _result(
        any(s["changed"] for s in steps.values()),
        f"VCF management components full upgrade to {target} completed/submitted",
        {"ready": ready["data"], **{k: v["data"] for k, v in steps.items()}},
    )


def report(plan_id=None, **kwargs):
    client = _client(**kwargs)
    return _result(
        False,
        "VCF management components status collected",
        {
            "plan_id": client.get_upgrade_plan_id(plan_id),
            "available_versions": [release_version(r) for r in client.list_releases()],
            "components": [
                {
                    "type": c.get("componentType"),
                    "fqdn": c.get("fqdn"),
                    "version": c.get("currentVersion") or c.get("version"),
                }
                for c in client.list_components()
            ],
        },
    )


def inspect_api(**kwargs):
    """Return the raw Fleet Lifecycle responses the upgrade logic depends on, for troubleshooting."""
    client = _client(**kwargs)
    paths = (
        "/fleet-lcm/v1/components",
        "/fleet-lcm/v1/upgrade-plans",
        "/fleet-lcm/v1/release-versions/target-versions",
    )
    data = {}
    for path in paths:
        try:
            data[path] = client.request("GET", path)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            data[path] = f"ERROR: {exc}"
    return _result(False, "Raw Fleet Lifecycle responses collected", data)
