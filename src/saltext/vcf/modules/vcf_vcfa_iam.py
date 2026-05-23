"""Execution module for VCF Automation IAM role bindings."""

from saltext.vcf.clients import vcfa_iam as c

__virtualname__ = "vcf_vcfa_iam"


def __virtual__():
    return __virtualname__


def list_orgs(profile=None):
    """List orgs the caller can see.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_iam.list_orgs
    """
    return c.list_orgs(__opts__, profile=profile)


def get_org(org_id, profile=None):
    """Get org metadata."""
    return c.get_org(__opts__, org_id, profile=profile)


def get_org_or_none(org_id, profile=None):
    """Get org metadata, or ``None`` on 404."""
    return c.get_org_or_none(__opts__, org_id, profile=profile)


def list_users(org_id, profile=None):
    """List users in an org."""
    return c.list_users(__opts__, org_id, profile=profile)


def get_user_roles(org_id, user_id, profile=None):
    """List role bindings for a user in an org."""
    return c.get_user_roles(__opts__, org_id, user_id, profile=profile)


def patch_user_roles(org_id, user_id, add=None, remove=None, profile=None):
    """Add/remove role bindings on a user.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_iam.patch_user_roles <org_id> <user_id> add='[{"name": "...", "resource": "..."}]'
    """
    return c.patch_user_roles(__opts__, org_id, user_id, add=add, remove=remove, profile=profile)
