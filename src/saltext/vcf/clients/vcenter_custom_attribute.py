"""Client for vCenter custom attribute (custom field) definitions via SOAP/pyVmomi.

Custom attributes are metadata key definitions managed globally by the
``CustomFieldsManager`` on the connected vCenter Server, optionally scoped
to a managed object type (e.g. ``VirtualMachine``, ``HostSystem``). Setting
a custom attribute's *value* on a specific entity is out of scope here.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _manager(opts, profile=None):
    return soap.content(opts, profile=profile).customFieldsManager


def _to_dict(field_def):
    return {
        "key": field_def.key,
        "name": field_def.name,
        "managed_object_type": getattr(field_def.managedObjectType, "__name__", None),
    }


def list_(opts, profile=None):
    """Return all custom attribute definitions."""
    return [_to_dict(f) for f in _manager(opts, profile=profile).field or []]


def get(opts, name, profile=None):
    """Return the custom attribute definition named *name*.

    Raises ``LookupError`` if not found.
    """
    for field_def in _manager(opts, profile=profile).field or []:
        if field_def.name == name:
            return _to_dict(field_def)
    raise LookupError(f"custom attribute {name!r} not found")


def get_or_none(opts, name, profile=None):
    try:
        return get(opts, name, profile=profile)
    except LookupError:
        return None


def add(opts, name, managed_object_type=None, profile=None):
    """Define a new custom attribute named *name*.

    *managed_object_type* restricts the attribute to that entity type (e.g.
    ``"VirtualMachine"``); omit for a global attribute available on any type.
    """
    mo_type = getattr(vim, managed_object_type) if managed_object_type else None
    field_def = _manager(opts, profile=profile).AddCustomFieldDef(name=name, moType=mo_type)
    return _to_dict(field_def)


def remove(opts, key, profile=None):
    """Remove the custom attribute definition with the given integer *key*."""
    _manager(opts, profile=profile).RemoveCustomFieldDef(key=int(key))
