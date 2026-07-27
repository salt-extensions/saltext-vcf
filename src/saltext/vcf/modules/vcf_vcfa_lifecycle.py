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


# -- patches (baseline management) ----------------------------------------


def list_patches(product_id, profile=None):
    """List installed + available patches for a product.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_lifecycle.list_patches <product_id>
    """
    return c.list_patches(__opts__, product_id, profile=profile)


def installed_patches(product_id, profile=None):
    """List currently-installed patches for a product.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_lifecycle.installed_patches <product_id>
    """
    return c.installed_patches(__opts__, product_id, profile=profile)


def available_patches(product_id, profile=None):
    """List patches available (not yet installed) for a product."""
    return c.available_patches(__opts__, product_id, profile=profile)


def installed_patch_versions(product_id, profile=None):
    """Return the version strings of every installed patch (short form)."""
    return c.installed_patch_versions(__opts__, product_id, profile=profile)


def find_patch(product_id, version, profile=None):
    """Return the patch record matching *version*, or ``None``."""
    return c.find_patch(__opts__, product_id, version, profile=profile)


def stage_patch(product_id, version, profile=None):
    """Stage (download) a patch for a product without installing.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_lifecycle.stage_patch <product_id> 9.0.1.2
    """
    return c.stage_patch(__opts__, product_id, version, profile=profile)


def apply_patch(product_id, version, options=None, profile=None):
    """Apply a patch — installs (stages if needed) *version* for *product_id*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_lifecycle.apply_patch <product_id> 9.0.1.2
    """
    return c.apply_patch(__opts__, product_id, version, options=options, profile=profile)


def baseline_check(product_id, allowed_versions, profile=None):
    """Compare installed patches against *allowed_versions*.

    Returns a dict::

        {"compliant": bool,
         "installed": ["9.0.1.2", ...],
         "allowed": [...],
         "in_baseline": ["9.0.1.2"],
         "out_of_baseline": ["9.0.1.1"]}

    Compliant is true when there is at least one installed patch and
    every installed patch matches an entry in *allowed_versions*.
    """
    installed = c.installed_patches(__opts__, product_id, profile=profile)
    in_baseline = []
    out_of_baseline = []
    for entry in installed:
        version = c.resolve_patch_version(entry)
        if version is None:
            continue
        if c.is_patch_allowed(entry, allowed_versions):
            in_baseline.append(version)
        else:
            out_of_baseline.append(version)
    installed_versions = [c.resolve_patch_version(e) for e in installed]
    installed_versions = [v for v in installed_versions if v]
    return {
        "compliant": bool(installed_versions) and not out_of_baseline,
        "installed": installed_versions,
        "allowed": list(allowed_versions),
        "in_baseline": in_baseline,
        "out_of_baseline": out_of_baseline,
    }
