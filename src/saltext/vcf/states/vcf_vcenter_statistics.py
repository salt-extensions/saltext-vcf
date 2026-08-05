"""State module for vCenter Server statistics collection intervals."""

from saltext.vcf.clients import vcenter_statistics as c

__virtualname__ = "vcf_vcenter_statistics"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def interval(name, enabled=None, interval_minutes=None, save_days=None, level=None, profile=None):
    """Ensure one of the four built-in statistics intervals matches the given values.

    *name* is one of ``past_day``, ``past_week``, ``past_month``, ``past_year``.
    Only the fields passed are enforced; omitted fields are left as-is.
    """
    ret = _ret(name)
    current = c.interval_get(__opts__, name, profile=profile)
    if current is None:
        ret["result"] = False
        ret["comment"] = f"unknown statistics interval {name!r}"
        return ret

    wanted = {
        k: v
        for k, v in {
            "enabled": enabled,
            "interval_minutes": interval_minutes,
            "save_days": save_days,
            "level": level,
        }.items()
        if v is not None
    }
    diff = {k: v for k, v in wanted.items() if current.get(k) != v}
    if not diff:
        ret["comment"] = f"{name} statistics interval already matches"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"{name} statistics interval would change: {diff}"
        return ret

    c.interval_set(
        __opts__,
        name,
        enabled=enabled,
        interval_minutes=interval_minutes,
        save_days=save_days,
        level=level,
        profile=profile,
    )
    ret["changes"] = {k: {"old": current.get(k), "new": v} for k, v in diff.items()}
    ret["comment"] = f"{name} statistics interval updated"
    return ret
