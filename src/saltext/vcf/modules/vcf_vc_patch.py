"""Execution module for vCenter's VAMI appliance-update REST API (VCSA self-patching).

Patches the vCenter Server Appliance itself: configure an update
repository, list/resolve pending updates, stage a build, run prechecks,
and install. See :mod:`saltext.vcf.clients.vc_patch` for the underlying
REST calls, and :mod:`saltext.vcf.states.vcf_vc_patch` for the
declarative/idempotent workflow.

Quick reference::

    # Repository + pending updates
    salt-call vcf_vc_patch.get_update_policy
    salt-call vcf_vc_patch.list_pending_updates
    salt-call vcf_vc_patch.get_pending_update 9.0.1.0.12345

    # Stage without monitoring (useful on flaky links — see monitor_stage below)
    salt-call vcf_vc_patch.stage 9.0.1.0.12345 monitor=false
    salt-call vcf_vc_patch.get_update_status
    salt-call vcf_vc_patch.get_staged_update

    # Install (requires the SSO admin password)
    salt-call vcf_vc_patch.install 9.0.1.0.12345 'VMware123!VMware123!'
"""

from saltext.vcf.clients import vc_patch as c

__virtualname__ = "vcf_vc_patch"


def __virtual__():
    return __virtualname__


def _cfg():
    pillar = __opts__.get("pillar", {})  # noqa: F821
    root = pillar.get("saltext.vcf", {}) or {}
    return root.get("vc_patch", {}) or {}


def get_update_policy(profile=None):
    """Get update policy.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vc_patch.get_update_policy

    """
    return c.get_update_policy(__opts__, profile=profile)


def get_repository_policy(profile=None):
    """Alias for :func:`get_update_policy`.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vc_patch.get_repository_policy

    """
    return get_update_policy(profile=profile)


def update_repository_policy(
    repository_url=None,
    auto_stage=None,
    certificate_check=None,
    check_schedule=None,
    repo_username=None,
    repo_password=None,
    profile=None,
):
    """Configure the update-repository policy.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vc_patch.update_repository_policy http://repo.example.com/vcsa/

    """
    cfg = _cfg()
    return c.set_update_policy(
        __opts__,
        repository_url or cfg.get("repository_url"),
        auto_stage=cfg.get("auto_stage", False) if auto_stage is None else auto_stage,
        certificate_check=(
            cfg.get("certificate_check", True) if certificate_check is None else certificate_check
        ),
        check_schedule=cfg.get("check_schedule") if check_schedule is None else check_schedule,
        repo_username=cfg.get("repo_username", "") if repo_username is None else repo_username,
        repo_password=cfg.get("repo_password", "") if repo_password is None else repo_password,
        profile=profile,
    )


def list_pending_updates(repository_url=None, source_type="LOCAL_AND_ONLINE", profile=None):
    """List pending updates.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vc_patch.list_pending_updates

    """
    cfg = _cfg()
    return c.list_pending_updates(
        __opts__, repository_url or cfg.get("repository_url"), source_type, profile=profile
    )


def check_updates(repository_url=None, source_type="LOCAL_AND_ONLINE", profile=None):
    """Alias for :func:`list_pending_updates`.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vc_patch.check_updates

    """
    return list_pending_updates(
        repository_url=repository_url, source_type=source_type, profile=profile
    )


def get_pending_update(version=None, profile=None):
    """Get pending update.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vc_patch.get_pending_update <version>

    """
    cfg = _cfg()
    return c.get_pending_update(__opts__, version or cfg.get("version"), profile=profile)


def list_upgradeable_components(version=None, profile=None):
    """List upgradeable components.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vc_patch.list_upgradeable_components <version>

    """
    cfg = _cfg()
    return c.list_upgradeable_components(__opts__, version or cfg.get("version"), profile=profile)


def get_update_status(profile=None):
    """Get update status.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vc_patch.get_update_status

    """
    return c.get_update_status(__opts__, profile=profile)


def get_staged_update(profile=None):
    """Get staged update.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vc_patch.get_staged_update

    """
    return c.get_staged_update(__opts__, profile=profile)


def delete_staged_update(profile=None):
    """Delete staged update.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vc_patch.delete_staged_update

    """
    return c.delete_staged_update(__opts__, profile=profile)


def get_update_history(profile=None):
    """Get update history.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vc_patch.get_update_history

    """
    return c.get_update_history(__opts__, profile=profile)


def precheck(version=None, component=None, profile=None):
    """Precheck.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vc_patch.precheck <version>

    """
    cfg = _cfg()
    return c.precheck(
        __opts__,
        version or cfg.get("version"),
        component=component if component is not None else cfg.get("component"),
        profile=profile,
    )


def stage(version=None, component=None, profile=None):
    """Stage.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vc_patch.stage <version>

    """
    cfg = _cfg()
    return c.stage(
        __opts__,
        version or cfg.get("version"),
        component=component if component is not None else cfg.get("component"),
        profile=profile,
    )


def install(version=None, sso_password=None, component=None, profile=None):
    """Install.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vc_patch.install <version> <sso_password>

    """
    cfg = _cfg()
    return c.install(
        __opts__,
        version or cfg.get("version"),
        sso_password if sso_password is not None else cfg.get("sso_password"),
        component=component if component is not None else cfg.get("component"),
        profile=profile,
    )


def resolve_update_version(repository_url=None, version=None, profile=None):
    """Resolve update version.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vc_patch.resolve_update_version

    """
    cfg = _cfg()
    resolved, _, _ = c.resolve_update_version(
        __opts__,
        repository_url=repository_url or cfg.get("repository_url"),
        version=version if version is not None else cfg.get("version"),
        profile=profile,
    )
    return resolved


def monitor_stage(
    poll_interval=50, timeout=3600, max_transient_errors=10, version=None, profile=None
):
    """Monitor stage.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vc_patch.monitor_stage

    """
    cfg = _cfg()
    return c.monitor_stage(
        __opts__,
        version=version if version is not None else cfg.get("version"),
        poll_interval=int(poll_interval),
        timeout=int(timeout),
        max_transient_errors=int(max_transient_errors),
        profile=profile,
    )


def monitor_install(poll_interval=120, timeout=7200, max_transient_errors=10, profile=None):
    """Monitor install.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vc_patch.monitor_install

    """
    return c.monitor_install(
        __opts__,
        poll_interval=int(poll_interval),
        timeout=int(timeout),
        max_transient_errors=int(max_transient_errors),
        profile=profile,
    )


def wait_for_staged_update(version=None, poll_interval=10, timeout=600, profile=None):
    """Wait for staged update.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vc_patch.wait_for_staged_update

    """
    cfg = _cfg()
    return c.wait_for_staged_update(
        __opts__,
        version=version if version is not None else cfg.get("version"),
        poll_interval=int(poll_interval),
        timeout=int(timeout),
        profile=profile,
    )
