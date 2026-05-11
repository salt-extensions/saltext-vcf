"""vCenter authorization roles via SOAP ``AuthorizationManager``.

REST (``/api/vcenter/...``) doesn't expose authorization role CRUD in
VCF 9.x; the SOAP ``AuthorizationManager`` is the only path.

Role identity model:

- Each role has a server-assigned integer ``roleId`` and a human ``name``.
- System roles (``Admin``, ``ReadOnly``, ``View``, ``Anonymous``, etc.) have
  the ``system`` flag set and cannot be modified or removed.
"""

from saltext.vmware.utils import vim as soap


def _mgr(opts, profile=None):
    return soap.authorization_manager(opts, profile=profile)


def list_(opts, profile=None):
    """Return a list of ``{role_id, name, system, info, privilege}`` dicts."""
    out = []
    for role in _mgr(opts, profile=profile).roleList:
        out.append(
            {
                "role_id": role.roleId,
                "name": role.name,
                "system": bool(role.system),
                "info_label": role.info.label if role.info else "",
                "info_summary": role.info.summary if role.info else "",
                "privilege": list(role.privilege or []),
            }
        )
    return out


def get(opts, name, profile=None):
    """Return the role record for *name*, raising ``LookupError`` if missing."""
    for role in _mgr(opts, profile=profile).roleList:
        if role.name == name:
            return {
                "role_id": role.roleId,
                "name": role.name,
                "system": bool(role.system),
                "info_label": role.info.label if role.info else "",
                "info_summary": role.info.summary if role.info else "",
                "privilege": list(role.privilege or []),
            }
    raise LookupError(f"role {name!r} not found")


def get_or_none(opts, name, profile=None):
    try:
        return get(opts, name, profile=profile)
    except LookupError:
        return None


def create(opts, name, privileges, profile=None):
    """Create a custom role with the given *privileges* list.

    Returns the new ``roleId``.
    """
    return _mgr(opts, profile=profile).AddAuthorizationRole(name=name, privIds=list(privileges))


def update(opts, name, privileges, profile=None):
    """Replace the privilege set on the role *name*."""
    mgr = _mgr(opts, profile=profile)
    role_id = _role_id_by_name(mgr, name)
    mgr.UpdateAuthorizationRole(roleId=role_id, newName=name, privIds=list(privileges))


def rename(opts, name, new_name, profile=None):
    mgr = _mgr(opts, profile=profile)
    role_id = _role_id_by_name(mgr, name)
    # Reuse current privilege set
    privileges = next(r.privilege for r in mgr.roleList if r.roleId == role_id)
    mgr.UpdateAuthorizationRole(roleId=role_id, newName=new_name, privIds=list(privileges or []))


def delete(opts, name, fail_if_used=True, profile=None):
    """Delete role *name*.

    When *fail_if_used* is ``True`` (default) the call raises if any
    permission still references the role. ``False`` forces removal and
    converts existing references to ``-1`` (no permission).
    """
    mgr = _mgr(opts, profile=profile)
    role_id = _role_id_by_name(mgr, name)
    mgr.RemoveAuthorizationRole(roleId=role_id, failIfUsed=fail_if_used)


def _role_id_by_name(mgr, name):
    for role in mgr.roleList:
        if role.name == name:
            return role.roleId
    raise LookupError(f"role {name!r} not found")


def list_privileges(opts, profile=None):
    """Catalog of every privilege known to vCenter."""
    out = []
    for priv in _mgr(opts, profile=profile).privilegeList:
        out.append(
            {
                "id": priv.privId,
                "name": priv.name,
                "group": priv.privGroupName,
                "on_parent": bool(priv.onParent),
            }
        )
    return out


def list_privilege_groups(opts, profile=None):
    return [
        {"id": pg.privGroupId, "name": pg.privGroupName}
        for pg in _mgr(opts, profile=profile).privilegeList
    ]
