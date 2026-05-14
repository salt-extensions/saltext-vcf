"""vSphere license management via ``LicenseManager`` and ``LicenseAssignmentManager``."""

from saltext.vmware.utils import vim as soap


def _lm(opts, profile=None):
    return soap.license_manager(opts, profile=profile)


def _lam(opts, profile=None):
    return soap.license_assignment_manager(opts, profile=profile)


def _to_dict(lic):
    return {
        "license_key": lic.licenseKey,
        "name": lic.name,
        "edition_key": lic.editionKey,
        "used": int(lic.used) if lic.used is not None else None,
        "total": int(lic.total) if lic.total is not None else None,
        "labels": {l.key: l.value for l in (lic.labels or [])},
        "properties": {p.key: p.value for p in (lic.properties or [])},
    }


def list_(opts, profile=None):
    """Return every license known to the LicenseManager."""
    return [_to_dict(lic) for lic in _lm(opts, profile=profile).licenses or []]


def get(opts, license_key, profile=None):
    for lic in _lm(opts, profile=profile).licenses or []:
        if lic.licenseKey == license_key:
            return _to_dict(lic)
    raise LookupError(f"license {license_key!r} not found")


def get_or_none(opts, license_key, profile=None):
    try:
        return get(opts, license_key, profile=profile)
    except LookupError:
        return None


def add(opts, license_key, labels=None, profile=None):
    """Register a new license. *labels* is an optional ``{key: value}`` dict."""
    lm = _lm(opts, profile=profile)
    from pyVmomi import vim  # local import keeps top-level deps minimal

    labels_obj = None
    if labels:
        labels_obj = [vim.KeyValue(key=k, value=v) for k, v in labels.items()]
    lic = lm.AddLicense(licenseKey=license_key, labels=labels_obj)
    return _to_dict(lic)


def remove(opts, license_key, profile=None):
    _lm(opts, profile=profile).RemoveLicense(licenseKey=license_key)
    return True


def update_label(opts, license_key, label_key, label_value, profile=None):
    """Set a single label on an existing license."""
    _lm(opts, profile=profile).UpdateLicenseLabel(
        licenseKey=license_key, labelKey=label_key, labelValue=label_value
    )
    return True


def assigned_list(opts, entity_id=None, profile=None):
    """List license assignments. If *entity_id* given, filter to that entity."""
    lam = _lam(opts, profile=profile)
    out = []
    for a in lam.QueryAssignedLicenses(entityId=entity_id) or []:
        out.append(
            {
                "entity_id": a.entityId,
                "scope": a.scope,
                "entity_display_name": a.entityDisplayName,
                "assigned_license": _to_dict(a.assignedLicense),
            }
        )
    return out


def assign(opts, entity_id, license_key, *, name=None, profile=None):
    """Assign *license_key* to *entity_id* (e.g. a host moId or vCenter instance UUID)."""
    info = _lam(opts, profile=profile).UpdateAssignedLicense(
        entity=entity_id, licenseKey=license_key, entityDisplayName=name
    )
    return _to_dict(info)


def unassign(opts, entity_id, profile=None):
    _lam(opts, profile=profile).RemoveAssignedLicense(entityId=entity_id)
    return True
