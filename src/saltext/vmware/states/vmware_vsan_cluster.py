"""State module for vSAN cluster configuration."""

from saltext.vmware.clients import vsan_cluster as c

__virtualname__ = "vmware_vsan_cluster"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def configured(
    name,
    *,
    enabled=None,
    dedup_compression_enabled=None,
    encryption_enabled=None,
    auto_claim_storage=None,
    profile=None,
):
    """Ensure cluster *name* (MoId or display name) has the specified vSAN config.

    Each field is optional; only those provided are reconciled. Unset
    fields are left as-is.
    """
    ret = _ret(name)
    current = c.get(__opts__, name, profile=profile) or {}

    changes = {}
    drift = {}
    for field, desired in (
        ("enabled", enabled),
        ("dedup_compression_enabled", dedup_compression_enabled),
        ("encryption_enabled", encryption_enabled),
        ("auto_claim_storage", auto_claim_storage),
    ):
        if desired is None:
            continue
        actual = current.get(field)
        if bool(actual) != bool(desired):
            drift[field] = {"old": actual, "new": bool(desired)}

    if not drift:
        ret["comment"] = f"vSAN cluster {name} already configured"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"vSAN cluster {name} would change: {', '.join(drift)}"
        return ret

    task_id = c.reconfigure(
        __opts__,
        name,
        enabled=enabled,
        dedup_compression_enabled=dedup_compression_enabled,
        encryption_enabled=encryption_enabled,
        auto_claim_storage=auto_claim_storage,
        profile=profile,
    )
    changes.update(drift)
    changes["task_id"] = task_id
    ret["changes"] = changes
    ret["comment"] = f"vSAN cluster {name} reconfigure submitted (task={task_id})"
    return ret
