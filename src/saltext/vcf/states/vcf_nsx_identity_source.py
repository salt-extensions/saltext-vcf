"""State module for NSX Manager LDAP/AD identity sources.

Identity sources are looked up by the caller-supplied *name* (matched against
the ``name`` field returned by NSX). Idempotency: *present* diffs only the
caller-supplied fields in *spec* against the current object, so opaque
server-populated attributes (``_revision``, ``id``, ...) do not trigger churn.
The ``password`` field is always considered opaque — because NSX will not
return it — and is included in updates whenever the caller supplies it.
"""

from saltext.vcf.clients import nsx_identity_source as c

__virtualname__ = "vcf_nsx_identity_source"

# Fields the API never echoes back; these are still forwarded on update
# whenever the caller supplied a value.
_OPAQUE_FIELDS = ("password",)


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def _find_by_name(opts, name, profile=None):
    listed = c.list_(opts, profile=profile) or {}
    for entry in listed.get("results") or []:
        if entry.get("name") == name:
            return entry
    return None


def _diff(current, spec):
    """Return the subset of *spec* whose values differ from *current*.

    Opaque fields (e.g. ``password``) always count as a diff when supplied.
    """
    changes = {}
    for key, value in spec.items():
        if key in _OPAQUE_FIELDS:
            changes[key] = {"old": "<opaque>", "new": "<opaque>"}
            continue
        if current.get(key) != value:
            changes[key] = {"old": current.get(key), "new": value}
    return changes


def present(name, spec, profile=None):
    """Ensure an LDAP identity source named *name* exists matching *spec*.

    *spec* is a dict of the NSX identity-source fields (``type``,
    ``domain_name``, ``base_dn``, ``ldap_servers``, ``bind_identity``,
    ``password``, ``user_search_filter``, ...). ``name`` is injected
    automatically.
    """
    ret = _ret(name)
    body = dict(spec)
    body["name"] = name
    current = _find_by_name(__opts__, name, profile=profile)

    if current is not None:
        changes = _diff(current, body)
        # Ignore no-op self-comparison of the name key
        changes.pop("name", None)
        if not changes:
            ret["comment"] = f"Identity source {name} already matches"
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["changes"] = changes
            ret["comment"] = f"Identity source {name} would be updated"
            return ret
        merged = dict(current)
        merged.update(body)
        c.update(__opts__, current["id"], merged, profile=profile)
        ret["changes"] = changes
        ret["comment"] = f"Identity source {name} updated"
        return ret

    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Identity source {name} would be created"
        return ret
    c.create(__opts__, body, profile=profile)
    ret["changes"] = {"new": name}
    ret["comment"] = f"Identity source {name} created"
    return ret


def absent(name, profile=None):
    """Ensure no LDAP identity source is registered under *name*."""
    ret = _ret(name)
    current = _find_by_name(__opts__, name, profile=profile)
    if current is None:
        ret["comment"] = f"Identity source {name} is already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Identity source {name} would be deleted"
        return ret
    c.delete(__opts__, current["id"], profile=profile)
    ret["changes"] = {"deleted": name}
    ret["comment"] = f"Identity source {name} deleted"
    return ret
