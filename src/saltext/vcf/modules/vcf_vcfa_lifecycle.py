"""Execution module for VCF Automation lifecycle management."""

from saltext.vcf.clients import vcfa_lifecycle as c

__virtualname__ = "vcf_vcfa_lifecycle"


def __virtual__():
    return __virtualname__


# -- products / versions ---------------------------------------------------


def list_products(profile=None):
    """List installed products.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_lifecycle.list_products
    """
    return c.list_products(__opts__, profile=profile)


def get_product(product_id, profile=None):
    """Get one product by id."""
    return c.get_product(__opts__, product_id, profile=profile)


def get_product_or_none(product_id, profile=None):
    """Get one product by id, or ``None`` on 404."""
    return c.get_product_or_none(__opts__, product_id, profile=profile)


def list_versions(product_id, profile=None):
    """List installed + available versions for a product."""
    return c.list_versions(__opts__, product_id, profile=profile)


# -- upgrades --------------------------------------------------------------


def list_upgrades(profile=None):
    """List upgrade requests.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_lifecycle.list_upgrades
    """
    return c.list_upgrades(__opts__, profile=profile)


def get_upgrade(upgrade_id, profile=None):
    """Get one upgrade by id."""
    return c.get_upgrade(__opts__, upgrade_id, profile=profile)


def get_upgrade_or_none(upgrade_id, profile=None):
    """Get one upgrade by id, or ``None`` on 404."""
    return c.get_upgrade_or_none(__opts__, upgrade_id, profile=profile)


def start_upgrade(upgrade_spec, profile=None):
    """Submit an upgrade request.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_lifecycle.start_upgrade '{"productId": "...", "targetVersion": "..."}'
    """
    return c.start_upgrade(__opts__, upgrade_spec, profile=profile)


def cancel_upgrade(upgrade_id, profile=None):
    """Cancel an upgrade."""
    return c.cancel_upgrade(__opts__, upgrade_id, profile=profile)


def retry_upgrade(upgrade_id, profile=None):
    """Retry a failed upgrade."""
    return c.retry_upgrade(__opts__, upgrade_id, profile=profile)


def resume_upgrade(upgrade_id, profile=None):
    """Resume a paused upgrade."""
    return c.resume_upgrade(__opts__, upgrade_id, profile=profile)


def wait_for_upgrade(upgrade_id, timeout=7200, poll_interval=30, profile=None):
    """Block until an upgrade reaches a terminal state.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_lifecycle.wait_for_upgrade <upgrade_id>
    """
    return c.wait_for_upgrade(
        __opts__, upgrade_id, timeout=timeout, poll_interval=poll_interval, profile=profile
    )


# -- snapshots -------------------------------------------------------------


def list_snapshots(profile=None):
    """List system snapshots."""
    return c.list_snapshots(__opts__, profile=profile)


def get_snapshot(snapshot_id, profile=None):
    """Get one snapshot by id."""
    return c.get_snapshot(__opts__, snapshot_id, profile=profile)


def get_snapshot_or_none(snapshot_id, profile=None):
    """Get one snapshot by id, or ``None`` on 404."""
    return c.get_snapshot_or_none(__opts__, snapshot_id, profile=profile)


def create_snapshot(snapshot_spec, profile=None):
    """Take a system snapshot.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_lifecycle.create_snapshot '{"name": "pre-upgrade", "includeData": true}'
    """
    return c.create_snapshot(__opts__, snapshot_spec, profile=profile)


def delete_snapshot(snapshot_id, profile=None):
    """Delete a snapshot."""
    return c.delete_snapshot(__opts__, snapshot_id, profile=profile)


def restore_snapshot(snapshot_id, profile=None):
    """Restore the system to a snapshot."""
    return c.restore_snapshot(__opts__, snapshot_id, profile=profile)
