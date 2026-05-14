"""State module for vCenter scheduled tasks."""

from saltext.vmware.clients import vim_scheduled_task as c

__virtualname__ = "vmware_vim_scheduled_task"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def present(name, entity, spec, profile=None):
    """Ensure a scheduled task with *name* exists on *entity*.

    Match is by ``spec.name`` field; if a task with the same name exists,
    no change is made (idempotency check on existence only — full spec
    diff is not attempted because the SOAP schema is open-ended).
    """
    ret = _ret(name)
    spec_name = spec.get("name", name)
    existing = c.get_or_none(__opts__, spec_name, profile=profile)
    if existing is not None:
        ret["comment"] = f"scheduled task {spec_name!r} already present"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"scheduled task {spec_name!r} would be created on {entity}"
        return ret
    task_id = c.create(__opts__, entity, spec, profile=profile)
    ret["changes"] = {"created": task_id}
    ret["comment"] = f"scheduled task {spec_name!r} created"
    return ret


def absent(name, profile=None):
    """Ensure scheduled task *name* is gone."""
    ret = _ret(name)
    existing = c.get_or_none(__opts__, name, profile=profile)
    if existing is None:
        ret["comment"] = f"scheduled task {name!r} already absent"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"scheduled task {name!r} would be removed"
        return ret
    c.delete(__opts__, name, profile=profile)
    ret["changes"] = {"removed": existing["id"]}
    ret["comment"] = f"scheduled task {name!r} removed"
    return ret
