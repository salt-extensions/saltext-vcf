"""VCF Automation — project membership.

VCFA stores project membership as four arrays on the project document:

* ``administrators``
* ``members``
* ``viewers``
* ``supervisors``

Each entry has shape ``{"email": "user@example.com", "type": "user"|"group"}``.
This client mutates membership via PATCH on the project so callers
don't have to GET/edit/PATCH themselves.
"""

from saltext.vcf.clients import vcfa_project
from saltext.vcf.utils import vcfa

ROLES = ("administrators", "members", "viewers", "supervisors")


def list_members(opts, project_id, role=None, profile=None):
    """Return the membership of the project.

    If *role* is given, return just that role's array. Otherwise return
    a dict mapping each role to its array.
    """
    if role is not None and role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}, got {role!r}")
    project = vcfa_project.get(opts, project_id, profile=profile)
    if role is not None:
        return list(project.get(role, []) or [])
    return {r: list(project.get(r, []) or []) for r in ROLES}


def add_member(opts, project_id, role, email, *, member_type="user", profile=None):
    """Add an entry to a project role. Idempotent — no-op if already present."""
    if role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}, got {role!r}")
    project = vcfa_project.get(opts, project_id, profile=profile)
    current = list(project.get(role, []) or [])
    if any(m.get("email") == email for m in current):
        return project
    current.append({"email": email, "type": member_type})
    return vcfa.api_patch(
        opts, f"/iaas/api/projects/{project_id}", body={role: current}, profile=profile
    )


def remove_member(opts, project_id, role, email, profile=None):
    """Remove an entry from a project role. Idempotent — no-op if absent."""
    if role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}, got {role!r}")
    project = vcfa_project.get(opts, project_id, profile=profile)
    current = list(project.get(role, []) or [])
    filtered = [m for m in current if m.get("email") != email]
    if len(filtered) == len(current):
        return project
    return vcfa.api_patch(
        opts, f"/iaas/api/projects/{project_id}", body={role: filtered}, profile=profile
    )


def set_members(opts, project_id, role, emails, *, member_type="user", profile=None):
    """Replace a role's membership wholesale.

    *emails* is the full desired list; this call PATCHes the project
    with ``{role: [{email, type}, ...]}``.
    """
    if role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}, got {role!r}")
    body = {role: [{"email": e, "type": member_type} for e in emails]}
    return vcfa.api_patch(opts, f"/iaas/api/projects/{project_id}", body=body, profile=profile)
