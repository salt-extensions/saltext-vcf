"""Execution module for VCF Automation project membership."""

from saltext.vcf.clients import vcfa_project_user as c

__virtualname__ = "vcf_vcfa_project_user"


def __virtual__():
    return __virtualname__


def list_members(project_id, role=None, profile=None):
    """List project members.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_project_user.list_members <project_id>
        salt '*' vcf_vcfa_project_user.list_members <project_id> role=administrators
    """
    return c.list_members(__opts__, project_id, role=role, profile=profile)


def add_member(project_id, role, email, member_type="user", profile=None):
    """Add a user/group to a project role. Idempotent.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_project_user.add_member <project_id> members user@example.com
    """
    return c.add_member(__opts__, project_id, role, email, member_type=member_type, profile=profile)


def remove_member(project_id, role, email, profile=None):
    """Remove a user/group from a project role. Idempotent."""
    return c.remove_member(__opts__, project_id, role, email, profile=profile)


def set_members(project_id, role, emails, member_type="user", profile=None):
    """Replace a role's membership wholesale."""
    return c.set_members(
        __opts__, project_id, role, emails, member_type=member_type, profile=profile
    )
