"""VCF upgrades through SDDC Manager. Configure ``saltext.vcf:sddc_manager`` and ``saltext.vcf:vcf_upgrade`` pillar."""

import logging

from saltext.vcf.utils.vcf_upgrade_orchestrator import VcfUpgradeOrchestrator
from saltext.vcf.utils.vcf_upgrade_transport import CommandExecutionError

log = logging.getLogger(__name__)
__virtualname__ = "vcf_upgrade"


def __virtual__():
    return __virtualname__


def _provider(profile=None, **kwargs):
    if kwargs:
        raise CommandExecutionError(
            f"Unsupported options: {sorted(kwargs)}; use sddc_manager pillar/profile"
        )
    from saltext.vcf.clients.vcf_upgrade import get_provider

    return get_provider(__opts__, profile=profile)


def _u():
    root = __opts__.get("pillar", {}).get("saltext.vcf") or __opts__.get("saltext.vcf") or {}
    return root.get("vcf_upgrade", {}) or {}


def _orch(checkpoint_file=None, **kwargs):
    path = (
        checkpoint_file
        or _u().get("checkpoint_file")
        or (__opts__.get("cachedir", "/var/cache/salt/minion") + "/vcf-upgrade.json")
    )
    return VcfUpgradeOrchestrator(_provider(**kwargs), log, path)


def list_target_versions(
    component_type=None, domain_id=None, current_version=None, min_bump=None, **kwargs
):
    """List release candidates; this is discovery, not upgrade-path approval.

    CLI Example:

    .. code-block:: bash

        salt-call vcf_upgrade.list_target_versions
    """
    cfg = _u()
    return _provider(**kwargs).list_target_versions(
        component_type or cfg.get("component_type", "SDDC_MANAGER"),
        domain_id or cfg.get("domain_id"),
        current_version,
        min_bump or cfg.get("min_bump", "MAJOR_OR_MINOR"),
    )


def list_bundle_builds(release_version, component_type=None, **kwargs):
    """List exact builds for a release and component.

    CLI Example:

    .. code-block:: bash

        salt-call vcf_upgrade.list_bundle_builds 9.1.0.0
    """
    return _provider(**kwargs).list_bundle_builds(
        release_version, component_type or _u().get("component_type", "SDDC_MANAGER")
    )


def download_bundle(
    component_type=None,
    target_version=None,
    wait=None,
    timeout=None,
    poll_interval=None,
    dry_run=False,
    **kwargs,
):
    """Download an explicit target bundle; avoid resubmitting active downloads.

    CLI Example:

    .. code-block:: bash

        salt-call vcf_upgrade.download_bundle
    """
    cfg = _u()
    life = cfg.get("lifecycle", {})
    return _orch(**kwargs).bundle_downloaded(
        component_type or cfg.get("component_type", "SDDC_MANAGER"),
        target_version or cfg.get("target_build") or cfg.get("target_version"),
        life.get("wait_for_bundle", True) if wait is None else wait,
        life.get("bundle_timeout_seconds", 14400) if timeout is None else timeout,
        life.get("poll_interval_seconds", 60) if poll_interval is None else poll_interval,
        dry_run,
    )


def plan(component_type=None, target_version=None, domain_id=None, **kwargs):
    """Resolve a downloaded bundle and domain without submitting an upgrade.

    CLI Example:

    .. code-block:: bash

        salt-call vcf_upgrade.plan
    """
    cfg = _u()
    return _provider(**kwargs).plan(
        component_type or cfg.get("component_type", "SDDC_MANAGER"),
        target_version or cfg.get("target_build") or cfg.get("target_version"),
        domain_id or cfg.get("domain_id"),
    )


def _single(
    component_type,
    target_version,
    domain_id,
    draft_mode,
    schedule_for_later,
    scheduled_timestamp,
    options,
    checkpoint_file,
    dry_run,
    create_only,
    kwargs,
):
    cfg = _u()
    merged = dict(cfg.get("options") or {})
    merged.update(options or {})
    spec = {
        "type": component_type or cfg.get("component_type", "SDDC_MANAGER"),
        "options": merged,
        "draft_mode": cfg.get("draft_mode") if draft_mode is None else draft_mode,
        "schedule_for_later": (
            cfg.get("schedule_for_later", False)
            if schedule_for_later is None
            else schedule_for_later
        ),
        "scheduled_timestamp": scheduled_timestamp or cfg.get("scheduled_timestamp"),
    }
    return _orch(checkpoint_file, **kwargs).sequence(
        [spec],
        target_version or cfg.get("target_build") or cfg.get("target_version"),
        domain_id or cfg.get("domain_id"),
        cfg.get("lifecycle"),
        dry_run=dry_run,
        create_only=create_only,
    )


def create_upgrade(
    component_type=None,
    target_version=None,
    domain_id=None,
    draft_mode=None,
    schedule_for_later=None,
    scheduled_timestamp=None,
    options=None,
    checkpoint_file=None,
    dry_run=False,
    **kwargs,
):
    """Ensure one checkpointed creation. Direct-mode SDDC Manager creation starts execution.

    CLI Example:

    .. code-block:: bash

        salt-call vcf_upgrade.create_upgrade
    """
    return _single(
        component_type,
        target_version,
        domain_id,
        draft_mode,
        schedule_for_later,
        scheduled_timestamp,
        options,
        checkpoint_file,
        dry_run,
        True,
        kwargs,
    )


def execute_upgrade(
    upgrade_id, schedule_for_later=None, scheduled_timestamp=None, dry_run=False, **kwargs
):
    """Commit a draft explicitly; whole workflows run prechecks before this step.

    CLI Example:

    .. code-block:: bash

        salt-call vcf_upgrade.execute_upgrade UPGRADE_ID
    """
    cfg = _u()
    return _orch(**kwargs).upgrade_executed(
        upgrade_id,
        cfg.get("schedule_for_later", False) if schedule_for_later is None else schedule_for_later,
        scheduled_timestamp or cfg.get("scheduled_timestamp"),
        dry_run,
    )


def get_upgrade_status(upgrade_id, **kwargs):
    """Read upgrade status without mutation.

    CLI Example:

    .. code-block:: bash

        salt-call vcf_upgrade.get_upgrade_status UPGRADE_ID
    """
    return _provider(**kwargs).upgrade_status(upgrade_id)


def wait_for_upgrade(upgrade_id, timeout=None, poll_interval=None, **kwargs):
    """Monitor an upgrade with bounded polling.

    CLI Example:

    .. code-block:: bash

        salt-call vcf_upgrade.wait_for_upgrade UPGRADE_ID
    """
    life = _u().get("lifecycle", {})
    return _orch(**kwargs).upgrade_monitored(
        upgrade_id,
        life.get("upgrade_timeout_seconds", 43200) if timeout is None else timeout,
        life.get("poll_interval_seconds", 60) if poll_interval is None else poll_interval,
    )


def run(
    component_type=None,
    target_version=None,
    domain_id=None,
    draft_mode=None,
    schedule_for_later=None,
    scheduled_timestamp=None,
    options=None,
    checkpoint_file=None,
    dry_run=False,
    **kwargs,
):
    """Run/resume one component through download, precheck, execution and verification.

    CLI Example:

    .. code-block:: bash

        salt-call vcf_upgrade.run
    """
    return _single(
        component_type,
        target_version,
        domain_id,
        draft_mode,
        schedule_for_later,
        scheduled_timestamp,
        options,
        checkpoint_file,
        dry_run,
        False,
        kwargs,
    )


def start_precheck(upgrade_id, domain_id, bundle_id, component_type, **kwargs):
    """Query and trigger the selected upgrade checks.

    CLI Example:

    .. code-block:: bash

        salt-call vcf_upgrade.start_precheck UPGRADE_ID DOMAIN_ID BUNDLE_ID VCENTER
    """
    return _provider(**kwargs).start_precheck(upgrade_id, domain_id, bundle_id, component_type)


def get_precheck_status(check_set_id, **kwargs):
    """Read check-set status and validation findings.

    CLI Example:

    .. code-block:: bash

        salt-call vcf_upgrade.get_precheck_status CHECK_SET_ID
    """
    return _provider(**kwargs).precheck_status(check_set_id)


def wait_for_precheck(check_set_id, timeout=7200, poll_interval=60, fail_on_error=True, **kwargs):
    """Wait for validation evidence and reject failures by default.

    CLI Example:

    .. code-block:: bash

        salt-call vcf_upgrade.wait_for_precheck CHECK_SET_ID
    """
    return _provider(**kwargs).wait_precheck(check_set_id, timeout, poll_interval, fail_on_error)


def run_sequence(
    components=None,
    target_version=None,
    domain_id=None,
    checkpoint_file=None,
    reset_checkpoint=False,
    dry_run=False,
    **kwargs,
):
    """Run/resume an explicitly ordered component sequence.

    CLI Example:

    .. code-block:: bash

        salt-call vcf_upgrade.run_sequence
    """
    cfg = _u()
    sequence = components if components is not None else cfg.get("sequence")
    return _orch(checkpoint_file, **kwargs).sequence(
        sequence,
        target_version or cfg.get("target_build") or cfg.get("target_version"),
        domain_id or cfg.get("domain_id"),
        cfg.get("lifecycle"),
        dry_run,
        reset_checkpoint,
    )
