"""vCenter custom attributes (Custom Fields) via SOAP CustomFieldsManager.

REST exposes tags; custom attributes are a separate, older mechanism still
heavily used in compliance/automation workflows. SOAP-only.
"""

from pyVmomi import vim

from saltext.vmware.utils import vim as soap


def list_(opts, profile=None):
    """Return all defined custom attribute definitions."""
    cfm = soap.custom_fields_manager(opts, profile=profile)
    return [
        {
            "key": f.key,
            "name": f.name,
            "managed_object_type": (f.managedObjectType.__name__ if f.managedObjectType else None),
        }
        for f in cfm.field
    ]


def get(opts, name, profile=None):
    """Return the custom attribute matching *name*, or None."""
    for f in list_(opts, profile=profile):
        if f["name"] == name:
            return f
    return None


def get_or_none(opts, name, profile=None):
    return get(opts, name, profile=profile)


def add(opts, name, managed_object_type=None, profile=None):
    """Define a new custom attribute.

    *managed_object_type* limits which entity kinds can have this attribute
    set on them — pass e.g. ``"VirtualMachine"``, ``"HostSystem"`` or
    leave None to allow all.
    """
    cfm = soap.custom_fields_manager(opts, profile=profile)
    type_class = None
    if managed_object_type:
        type_class = getattr(vim, managed_object_type, None)
    field = cfm.AddCustomFieldDef(name=name, moType=type_class)
    return {"key": field.key, "name": field.name}


def remove(opts, name_or_key, profile=None):
    """Remove a custom attribute by name or key."""
    cfm = soap.custom_fields_manager(opts, profile=profile)
    key = None
    if isinstance(name_or_key, int):
        key = name_or_key
    else:
        for f in cfm.field:
            if f.name == name_or_key:
                key = f.key
                break
    if key is None:
        raise LookupError(f"custom attribute {name_or_key!r} not found")
    cfm.RemoveCustomFieldDef(key=key)


def set_value(opts, entity_mo_id, name, value, entity_type=None, profile=None):
    """Set the value of *name* on *entity_mo_id* (a VM, host, etc.)."""
    cfm = soap.custom_fields_manager(opts, profile=profile)
    si = soap.get_service_instance(opts, profile=profile)
    type_class = getattr(vim, entity_type or "VirtualMachine", vim.VirtualMachine)
    entity = type_class(entity_mo_id, si._stub)  # noqa: SLF001
    # Look up key by name
    key = None
    for f in cfm.field:
        if f.name == name:
            key = f.key
            break
    if key is None:
        raise LookupError(f"custom attribute {name!r} not defined")
    cfm.SetField(entity=entity, key=key, value=value)
