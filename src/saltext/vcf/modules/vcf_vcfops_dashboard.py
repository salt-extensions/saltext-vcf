"""Execution module for VCF Operations dashboards."""

from saltext.vcf.clients import vcfops_dashboard as c

__virtualname__ = "vcf_vcfops_dashboard"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List every dashboard visible to the configured user.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_dashboard.list_
    """
    return c.list_(__opts__, profile=profile)


def get(dashboard_id, profile=None):
    """Return the dashboard identified by ``dashboard_id``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_dashboard.get <dashboard_id>
    """
    return c.get(__opts__, dashboard_id, profile=profile)


def get_or_none(dashboard_id, profile=None):
    """Like :func:`get` but returns ``None`` when no match.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_dashboard.get_or_none <dashboard_id>
    """
    return c.get_or_none(__opts__, dashboard_id, profile=profile)


def create(dashboard_spec, profile=None):
    """Create a new dashboard from ``dashboard_spec``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_dashboard.create <dashboard_spec>
    """
    return c.create(__opts__, dashboard_spec, profile=profile)


def update(dashboard_id, dashboard_spec, profile=None):
    """Replace the dashboard identified by ``dashboard_id`` with ``dashboard_spec``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_dashboard.update <dashboard_id> <dashboard_spec>
    """
    return c.update(__opts__, dashboard_id, dashboard_spec, profile=profile)


def delete(dashboard_id, profile=None):
    """Delete the dashboard identified by ``dashboard_id``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_dashboard.delete <dashboard_id>
    """
    return c.delete(__opts__, dashboard_id, profile=profile)


def share(dashboard_id, user_id, profile=None):
    """Share ``dashboard_id`` with the user identified by ``user_id``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_dashboard.share <dashboard_id> <user_id>
    """
    return c.share(__opts__, dashboard_id, user_id, profile=profile)


def import_(spec, profile=None):
    """Import a dashboard from a previously exported payload.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_dashboard.import_ <spec>
    """
    return c.import_(__opts__, spec, profile=profile)
