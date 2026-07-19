"""State module for vCenter's VAMI appliance-update REST API (VCSA self-patching).

Drives the vCenter Server Appliance's own update lifecycle: configure an
update repository, stage a resolved version (idempotent — a no-op if that
version is already staged), run prechecks, then install.

Inputs default from pillar ``saltext.vcf:vc_patch`` when not passed
explicitly — see :mod:`saltext.vcf.clients.vc_patch` for the underlying
REST calls.

Example::

    vc-repo:
      vcf_vc_patch.repository_configured:
        - repository_url: http://repo.example.com/vcsa/

    vc-staged:
      vcf_vc_patch.update_prepared:
        - version: "9.0.1.0.12345"
        - require:
          - vcf_vc_patch: vc-repo

    vc-installed:
      vcf_vc_patch.update_installed:
        - version: "9.0.1.0.12345"
        - sso_password: {{ pillar['vc_sso_password'] }}
        - require:
          - vcf_vc_patch: vc-staged
"""

import logging
import time

from saltext.vcf.clients import vc_patch as c

log = logging.getLogger(__name__)

__virtualname__ = "vcf_vc_patch"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def _fail(ret, exc):
    log.exception("vcf_vc_patch state %r failed", ret["name"])
    ret["result"] = False
    ret["comment"] = str(exc)
    return ret


def _cfg():
    pillar = __opts__.get("pillar", {})  # noqa: F821
    root = pillar.get("saltext.vcf", {}) or {}
    return root.get("vc_patch", {}) or {}


def _opt(explicit, cfg, key, default):
    """Return *explicit* unless it's ``None``, else pillar *cfg[key]*, else *default*."""
    return cfg.get(key, default) if explicit is None else explicit


def repository_configured(
    name,
    repository_url=None,
    auto_stage=None,
    certificate_check=None,
    check_schedule=None,
    repo_username=None,
    repo_password=None,
    profile=None,
):
    """Ensure the appliance's update-repository policy is configured.

    Not idempotency-checked — this PUT always fires; VAMI's policy-set
    action is itself idempotent server-side (it fully replaces the prior
    policy), so re-running with the same inputs is a safe no-op in effect.
    """
    ret = _ret(name)
    cfg = _cfg()
    repository_url = repository_url or cfg.get("repository_url")
    if not repository_url:
        return _fail(
            ret,
            ValueError(
                "repository_configured requires 'repository_url' "
                "(or pillar vc_patch:repository_url)"
            ),
        )

    if __opts__.get("test"):
        ret["result"] = None
        ret["comment"] = f"would configure update repository {repository_url!r}"
        return ret

    try:
        resp = c.set_update_policy(
            __opts__,
            repository_url,
            auto_stage=_opt(auto_stage, cfg, "auto_stage", False),
            certificate_check=_opt(certificate_check, cfg, "certificate_check", True),
            check_schedule=_opt(check_schedule, cfg, "check_schedule", None),
            repo_username=_opt(repo_username, cfg, "repo_username", ""),
            repo_password=_opt(repo_password, cfg, "repo_password", ""),
            profile=profile,
        )
    except Exception as exc:  # pylint: disable=broad-except
        return _fail(ret, exc)

    ret["changes"] = {"repository_url": repository_url, "response": resp}
    ret["comment"] = f"update repository configured: {repository_url!r}"
    return ret


def _precheck_when_allowed(profile, resolved, component, poll_interval, timeout):
    """Retry :func:`precheck <saltext.vcf.clients.vc_patch.precheck>` while staging finishes.

    VAMI refuses a precheck while staging is still in progress
    (``precheck.not_allowed_error``) — wait on a short monitor_stage cycle
    and retry until it's allowed, or *timeout* elapses.
    """
    deadline = time.time() + timeout
    last_exc = None
    while True:
        try:
            return c.precheck(__opts__, resolved, component=component, profile=profile)
        except Exception as exc:  # pylint: disable=broad-except
            last_exc = exc
            if not c.is_staging_in_progress_error(exc):
                raise
            log.info("precheck not allowed yet (staging in progress); waiting")
            c.monitor_stage(
                __opts__,
                version=resolved,
                poll_interval=min(10, poll_interval),
                timeout=min(600, timeout),
                profile=profile,
            )
        if time.time() > deadline:
            raise RuntimeError(
                f"Timed out waiting to run precheck after staging. Last error: {last_exc}"
            )


def update_prepared(  # pylint: disable=too-many-locals,too-many-branches
    name,
    repository_url=None,
    version=None,
    component=None,
    monitor=None,
    stage_timeout_seconds=None,
    poll_interval_seconds=None,
    max_transient_errors=None,
    force_stage=None,
    run_precheck=None,
    profile=None,
    **kwargs,
):
    """Ensure the resolved update *version* is staged on the appliance.

    Idempotent: if that version is already staged, this is a no-op unless
    *force_stage* is set. A client-side timeout during staging doesn't
    necessarily mean staging failed — falls back to polling
    :func:`get_staged_update <saltext.vcf.clients.vc_patch.get_staged_update>`
    to see if it completed anyway before treating it as an error.
    """
    ret = _ret(name)
    cfg = _cfg()
    repository_url = repository_url or cfg.get("repository_url")
    version = version if version is not None else cfg.get("version")
    component = component if component is not None else cfg.get("component")
    monitor = _opt(monitor, cfg, "monitor", True)
    stage_timeout = int(_opt(stage_timeout_seconds, cfg, "stage_timeout_seconds", 3600))
    poll_interval = int(_opt(poll_interval_seconds, cfg, "poll_interval_seconds", 50))
    max_transient = int(_opt(max_transient_errors, cfg, "max_transient_errors", 10))
    force_stage = _opt(force_stage, cfg, "force_stage", False)
    run_precheck = _opt(run_precheck, cfg, "run_precheck", True)

    data = {}
    try:
        if repository_url:
            # Never mutate the repository policy during a test=True dry-run.
            if __opts__.get("test"):
                data["repository_policy"] = {
                    "would_update": True,
                    "repository_url": repository_url,
                }
            else:
                data["repository_policy"] = c.set_update_policy(
                    __opts__, repository_url, profile=profile
                )
        resolved, pending_updates, pending_update = c.resolve_update_version(
            __opts__, repository_url=repository_url, version=version, profile=profile
        )
        data["resolved_version"] = resolved
        data["pending_update"] = pending_update

        try:
            staged = c.get_staged_update(__opts__, profile=profile)
        except Exception as exc:  # pylint: disable=broad-except
            log.debug("no matching staged update before stage: %s", exc)
            staged = None
        if c.staged_matches(staged, resolved) and not force_stage:
            ret["comment"] = f"VCSA update {resolved} is already staged"
            return ret

        if __opts__.get("test"):
            ret["result"] = None
            ret["comment"] = f"would stage VCSA update {resolved}"
            return ret

        try:
            data["stage"] = c.stage(__opts__, resolved, component=component, profile=profile)
        except Exception as exc:  # pylint: disable=broad-except
            if c.is_stage_timeout_error(exc):
                data["stage"] = c.wait_for_staged_update(
                    __opts__,
                    version=resolved,
                    poll_interval=min(10, poll_interval),
                    timeout=600,
                    profile=profile,
                )
            else:
                raise

        if monitor:
            data["monitor_stage"] = c.monitor_stage(
                __opts__,
                version=resolved,
                poll_interval=poll_interval,
                timeout=stage_timeout,
                max_transient_errors=max_transient,
                profile=profile,
            )
        if run_precheck:
            data["precheck"] = _precheck_when_allowed(
                profile, resolved, component, poll_interval, stage_timeout
            )
    except Exception as exc:  # pylint: disable=broad-except
        return _fail(ret, exc)

    ret["changes"] = data
    ret["comment"] = f"VCSA update prepared for version {resolved}"
    return ret


def update_installed(
    name,
    version=None,
    sso_password=None,
    component=None,
    monitor=None,
    install_timeout_seconds=None,
    poll_interval_seconds=None,
    max_transient_errors=None,
    profile=None,
    **kwargs,
):
    """Install a previously staged update *version*.

    Not idempotency-checked before install — only :func:`update_prepared`
    guards against redundant work; installing twice isn't a safe no-op to
    assume, so this always proceeds once called.
    """
    ret = _ret(name)
    cfg = _cfg()
    version = version if version is not None else cfg.get("version")
    sso_password = sso_password if sso_password is not None else cfg.get("sso_password")
    component = component if component is not None else cfg.get("component")
    monitor = _opt(monitor, cfg, "monitor", True)
    install_timeout = int(_opt(install_timeout_seconds, cfg, "install_timeout_seconds", 7200))
    poll_interval = int(_opt(poll_interval_seconds, cfg, "poll_interval_seconds", 120))
    max_transient = int(_opt(max_transient_errors, cfg, "max_transient_errors", 10))

    if not sso_password:
        return _fail(ret, ValueError("update_installed requires 'sso_password'"))

    try:
        resolved, _pending_updates, _pending_update = c.resolve_update_version(
            __opts__, version=version, profile=profile
        )

        if __opts__.get("test"):
            ret["result"] = None
            ret["comment"] = f"would install VCSA update {resolved}"
            return ret

        data = {
            "install": c.install(
                __opts__, resolved, sso_password, component=component, profile=profile
            )
        }
        if monitor:
            data["monitor_install"] = c.monitor_install(
                __opts__,
                poll_interval=poll_interval,
                timeout=install_timeout,
                max_transient_errors=max_transient,
                profile=profile,
            )
    except Exception as exc:  # pylint: disable=broad-except
        return _fail(ret, exc)

    ret["changes"] = data
    ret["comment"] = f"VCSA update install submitted for version {resolved}"
    return ret


def installed(  # pylint: disable=too-many-arguments
    name,
    repository_url=None,
    version=None,
    sso_password=None,
    component=None,
    monitor=None,
    stage_timeout_seconds=None,
    poll_interval_seconds=None,
    max_transient_errors=None,
    force_stage=None,
    run_precheck=None,
    install_timeout_seconds=None,
    profile=None,
):
    """Ensure *version* is staged and installed, in one call.

    Dispatches to :func:`update_prepared` under ``test=True`` (dry-run
    only stages), or :func:`update_installed` for a real run. Accepts the
    union of both functions' tuning parameters so a single SLS entry can
    drive either phase without needing two separate states.
    """
    if __opts__.get("test"):
        return update_prepared(
            name,
            repository_url=repository_url,
            version=version,
            component=component,
            monitor=monitor,
            stage_timeout_seconds=stage_timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
            max_transient_errors=max_transient_errors,
            force_stage=force_stage,
            run_precheck=run_precheck,
            profile=profile,
        )
    return update_installed(
        name,
        version=version,
        sso_password=sso_password,
        component=component,
        monitor=monitor,
        install_timeout_seconds=install_timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
        max_transient_errors=max_transient_errors,
        profile=profile,
    )
