"""Execution module for the NSX upgrade workflow."""

from saltext.vcf.clients import nsx_upgrade as c

__virtualname__ = "vcf_nsx_upgrade"


def __virtual__():
    return __virtualname__


# -- status / history -----------------------------------------------------


def status_summary(profile=None):
    """Return overall upgrade status.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_upgrade.status_summary
    """
    return c.status_summary(__opts__, profile=profile)


def history(profile=None):
    """Return previous upgrade runs."""
    return c.history(__opts__, profile=profile)


# -- plan controls --------------------------------------------------------


def start(profile=None):
    """Start the upgrade plan.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_upgrade.start
    """
    return c.start(__opts__, profile=profile)


def pause(profile=None):
    """Pause the upgrade plan."""
    return c.pause(__opts__, profile=profile)


def resume(profile=None):
    """Resume a paused plan."""
    return c.resume(__opts__, profile=profile)


def reset(profile=None):
    """Reset the plan to initial state."""
    return c.reset(__opts__, profile=profile)


def get_plan_settings(profile=None):
    """Get plan-level settings."""
    return c.get_plan_settings(__opts__, profile=profile)


def update_plan_settings(settings, profile=None):
    """Replace plan-level settings."""
    return c.update_plan_settings(__opts__, settings, profile=profile)


# -- upgrade unit groups --------------------------------------------------


def list_groups(profile=None):
    """List upgrade unit groups."""
    return c.list_groups(__opts__, profile=profile)


def get_group(group_id, profile=None):
    """Get one upgrade unit group."""
    return c.get_group(__opts__, group_id, profile=profile)


def get_group_or_none(group_id, profile=None):
    """Get one upgrade unit group, or ``None`` on 404."""
    return c.get_group_or_none(__opts__, group_id, profile=profile)


def create_group(group_spec, profile=None):
    """Create a custom upgrade unit group."""
    return c.create_group(__opts__, group_spec, profile=profile)


def update_group(group_id, group_spec, profile=None):
    """Update an upgrade unit group."""
    return c.update_group(__opts__, group_id, group_spec, profile=profile)


def delete_group(group_id, profile=None):
    """Delete an upgrade unit group."""
    return c.delete_group(__opts__, group_id, profile=profile)


# -- upgrade units --------------------------------------------------------


def list_units(group_id=None, profile=None):
    """List upgrade units, optionally filtered by group id."""
    return c.list_units(__opts__, group_id=group_id, profile=profile)


def get_unit(unit_id, profile=None):
    """Get one upgrade unit."""
    return c.get_unit(__opts__, unit_id, profile=profile)


def get_unit_or_none(unit_id, profile=None):
    """Get one upgrade unit, or ``None`` on 404."""
    return c.get_unit_or_none(__opts__, unit_id, profile=profile)


# -- bundles --------------------------------------------------------------


def list_bundles(profile=None):
    """List uploaded upgrade bundles."""
    return c.list_bundles(__opts__, profile=profile)


def get_bundle(bundle_id, profile=None):
    """Get one upgrade bundle."""
    return c.get_bundle(__opts__, bundle_id, profile=profile)


def get_bundle_or_none(bundle_id, profile=None):
    """Get one upgrade bundle, or ``None`` on 404."""
    return c.get_bundle_or_none(__opts__, bundle_id, profile=profile)


# -- waiter ---------------------------------------------------------------


def wait_for_completion(timeout=14400, poll_interval=30, profile=None):
    """Block until ``status-summary`` reports a terminal state.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_upgrade.wait_for_completion
    """
    return c.wait_for_completion(
        __opts__, timeout=timeout, poll_interval=poll_interval, profile=profile
    )
