"""State module for VCFA identity-provider registration.

Idempotent by IdP ``name`` (since the ``id`` is server-generated).
``present`` creates a new registration if none matches by name, or
PUTs an update when the current registration diverges from *spec*.
"""

from saltext.vcf.clients import vcfa_identity_provider as c

__virtualname__ = "vcf_vcfa_identity_provider"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def _diff(current, desired):
    """Return the shallow diff of *desired* against *current* for user-supplied keys."""
    diff = {}
    for key, want in desired.items():
        have = current.get(key)
        if have != want:
            diff[key] = {"old": have, "new": want}
    return diff


def present(name, org_id, spec, profile=None):
    """Ensure an IdP with ``name`` is registered under *org_id* matching *spec*.

    *spec* is the CSP body dict (must include ``type`` plus any
    type-specific fields). The ``name`` field of the spec is overridden
    by the state name for consistency.
    """
    ret = _ret(name)
    body = dict(spec)
    body["name"] = name

    current = c.find_by_name(__opts__, org_id, name, profile=profile)
    if current is not None:
        changes = _diff(current, body)
        if not changes:
            ret["comment"] = f"identity provider {name} already matches"
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"identity provider {name} would be updated"
            ret["changes"] = changes
            return ret
        c.identity_provider_update(__opts__, org_id, current["id"], body, profile=profile)
        ret["changes"] = changes
        ret["comment"] = f"identity provider {name} updated"
        return ret

    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"identity provider {name} would be created"
        return ret
    c.identity_provider_create(__opts__, org_id, body, profile=profile)
    ret["changes"] = {"new": name}
    ret["comment"] = f"identity provider {name} created"
    return ret


def absent(name, org_id, profile=None):
    """Ensure no IdP named *name* is registered under *org_id*."""
    ret = _ret(name)
    current = c.find_by_name(__opts__, org_id, name, profile=profile)
    if current is None:
        ret["comment"] = f"identity provider {name} is already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"identity provider {name} would be deleted"
        return ret
    c.identity_provider_delete(__opts__, org_id, current["id"], profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"identity provider {name} deleted"
    return ret
