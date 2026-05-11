"""vCenter object permissions via SOAP ``AuthorizationManager``.

A permission is a ``(entity, principal, role, propagate, group)`` tuple
attached to a managed object. SOAP is the only path — REST doesn't
expose ``Set/RetrieveEntityPermissions`` in VCF 9.x.
"""

from pyVmomi import vim

from saltext.vmware.utils import vim as soap


def _mgr(opts, profile=None):
    return soap.authorization_manager(opts, profile=profile)


def _resolve_entity(opts, entity_ref, profile=None):
    """Resolve an entity reference to a pyVmomi managed object.

    *entity_ref* can be either:
    - a vim managed-object reference (already resolved)
    - a string MoID (``"vm-100"``, ``"datacenter-2"``, ``"group-h5"``)
    - a string of the form ``"<type>:<moid>"`` (e.g. ``"VirtualMachine:vm-100"``)
    """
    if hasattr(entity_ref, "_moId"):
        return entity_ref
    if isinstance(entity_ref, str):
        si = soap.get_service_instance(opts, profile=profile)
        content_view = si.RetrieveContent()
        if ":" in entity_ref:
            type_name, moid = entity_ref.split(":", 1)
            ref_type = getattr(vim, type_name, None)
            if ref_type is None:
                raise ValueError(f"unknown vim type {type_name!r}")
            return ref_type(moid, content_view.searchIndex._stub)  # noqa: SLF001
        # Bare MoID: ask SearchIndex to resolve via standard view
        for vim_type in (
            vim.VirtualMachine,
            vim.Datacenter,
            vim.ClusterComputeResource,
            vim.ComputeResource,
            vim.HostSystem,
            vim.Folder,
            vim.ResourcePool,
            vim.Datastore,
            vim.Network,
        ):
            try:
                obj = vim_type(entity_ref, content_view.searchIndex._stub)  # noqa: SLF001
                _ = obj.name  # property fetch to validate
                return obj
            except vim.fault.ManagedObjectNotFound:
                continue
        raise LookupError(f"entity {entity_ref!r} not found")
    raise TypeError(f"unsupported entity_ref type {type(entity_ref).__name__}")


def _role_id_by_name(mgr, name):
    for role in mgr.roleList:
        if role.name == name:
            return role.roleId
    raise LookupError(f"role {name!r} not found")


def list_(opts, entity_ref, inherited=True, profile=None):
    """Return permissions attached to *entity_ref*.

    When *inherited* is ``True`` (default) permissions propagated from
    parent objects are included.
    """
    mgr = _mgr(opts, profile=profile)
    entity = _resolve_entity(opts, entity_ref, profile=profile)
    perms = mgr.RetrieveEntityPermissions(entity=entity, inherited=inherited)
    role_names = {r.roleId: r.name for r in mgr.roleList}
    return [
        {
            "entity_moid": p.entity._moId,  # noqa: SLF001
            "principal": p.principal,
            "group": bool(p.group),
            "role_id": p.roleId,
            "role": role_names.get(p.roleId, str(p.roleId)),
            "propagate": bool(p.propagate),
        }
        for p in (perms or [])
    ]


def set_(opts, entity_ref, principal, role, propagate=True, group=False, profile=None):
    """Set or update a single permission on *entity_ref*.

    *role* is the role's symbolic name (``"Admin"``, ``"ReadOnly"``, or a
    custom-role name).
    """
    mgr = _mgr(opts, profile=profile)
    entity = _resolve_entity(opts, entity_ref, profile=profile)
    role_id = _role_id_by_name(mgr, role)
    perm = vim.AuthorizationManager.Permission(
        entity=entity,
        principal=principal,
        group=bool(group),
        roleId=role_id,
        propagate=bool(propagate),
    )
    mgr.SetEntityPermissions(entity=entity, permission=[perm])


def remove(opts, entity_ref, principal, group=False, profile=None):
    """Remove the *(principal, group)* permission from *entity_ref*."""
    mgr = _mgr(opts, profile=profile)
    entity = _resolve_entity(opts, entity_ref, profile=profile)
    mgr.RemoveEntityPermission(entity=entity, user=principal, isGroup=bool(group))


def reset(opts, entity_ref, profile=None):
    """Reset all non-inherited permissions on *entity_ref* (rare; use with care)."""
    mgr = _mgr(opts, profile=profile)
    entity = _resolve_entity(opts, entity_ref, profile=profile)
    mgr.ResetEntityPermissions(entity=entity, permission=[])
