"""vSphere infrastructure profiles via ``HostProfileManager``.

Host profiles capture a reference ESXi config and replay it onto target
hosts. This client is read-mostly — listing existing profiles and reading
their export. Apply path is left for a future batch since it requires
host customization spec authoring.
"""

from saltext.vcf.utils import vim as soap


def _profile_mgr(opts, profile=None):
    return soap.content(opts, profile=profile).hostProfileManager


def _to_dict(p):
    return {
        "id": p._moId,  # noqa: SLF001
        "name": p.name,
        "description": getattr(p.config, "annotation", None) if p.config else None,
        "enabled": bool(getattr(p, "enabled", True)),
        "complyStatus": getattr(p, "complyStatus", None),
        "entity_count": len(list(p.entity or [])),
    }


def list_(opts, profile=None):
    """Return every host profile."""
    return [_to_dict(p) for p in _profile_mgr(opts, profile=profile).profile or []]


def get(opts, profile_id_or_name, profile=None):
    for p in _profile_mgr(opts, profile=profile).profile or []:
        if profile_id_or_name in (p._moId, p.name):  # noqa: SLF001
            return _to_dict(p)
    raise LookupError(f"host profile {profile_id_or_name!r} not found")


def get_or_none(opts, profile_id_or_name, profile=None):
    try:
        return get(opts, profile_id_or_name, profile=profile)
    except LookupError:
        return None


def export(opts, profile_id_or_name, profile=None):
    """Return the profile's XML export string."""
    for p in _profile_mgr(opts, profile=profile).profile or []:
        if profile_id_or_name in (p._moId, p.name):  # noqa: SLF001
            return p.ExportProfile()
    raise LookupError(f"host profile {profile_id_or_name!r} not found")


def check_compliance(opts, profile_id_or_name, profile=None):
    """Trigger a compliance check on the profile. Returns the vim.Task moId."""
    for p in _profile_mgr(opts, profile=profile).profile or []:
        if profile_id_or_name in (p._moId, p.name):  # noqa: SLF001
            task = p.CheckProfileCompliance_Task(entity=list(p.entity or []))
            return task._moId  # noqa: SLF001
    raise LookupError(f"host profile {profile_id_or_name!r} not found")
