"""vCenter Server statistics collection intervals (SOAP ``PerformanceManager``).

REST doesn't expose the vCenter Server "Statistics" settings (Configure >
General > Statistics in the vSphere Client — the four built-in "Past day /
week / month / year" collection intervals). They're only reachable through
``PerformanceManager.historicalInterval`` / ``UpdatePerfInterval``, the same
SOAP call PowerCLI's ``Get-/Set-VIStatInterval`` wraps.
"""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap

# Stable key -> built-in interval name, in the order the vSphere Client shows
# them. These four intervals always exist on every vCenter; there is no
# create/delete, only enable/disable and reconfigure.
_KEY_TO_NAME = {
    1: "past_day",
    2: "past_week",
    3: "past_month",
    4: "past_year",
}
_NAME_TO_KEY = {v: k for k, v in _KEY_TO_NAME.items()}


def _to_dict(interval):
    return {
        "key": interval.key,
        "enabled": bool(interval.enabled),
        "interval_minutes": interval.samplingPeriod // 60,
        "save_days": interval.length // 86400,
        "level": interval.level,
    }


def intervals_get(opts, profile=None):
    """Return ``{"past_day": {...}, "past_week": {...}, ...}`` of the four
    built-in intervals.
    """
    mgr = soap.perf_manager(opts, profile=profile)
    return {
        _KEY_TO_NAME[interval.key]: _to_dict(interval)
        for interval in mgr.historicalInterval
        if interval.key in _KEY_TO_NAME
    }


def interval_get(opts, name, profile=None):
    """Return the single named interval (``past_day``/``past_week``/``past_month``/``past_year``)."""
    return intervals_get(opts, profile=profile).get(name)


def interval_set(opts, name, enabled=None, interval_minutes=None, save_days=None, level=None, profile=None):
    """Update one built-in interval, leaving unspecified fields unchanged.

    *interval_minutes* is the sampling period; *save_days* is how long
    samples are retained before rolling up/aging out; *level* is the stats
    collection level (1-4, matching vCenter's Statistics Level column).
    """
    key = _NAME_TO_KEY.get(name)
    if key is None:
        raise ValueError(f"unknown statistics interval {name!r}; expected one of {sorted(_NAME_TO_KEY)}")

    mgr = soap.perf_manager(opts, profile=profile)
    current = next((i for i in mgr.historicalInterval if i.key == key), None)
    if current is None:
        raise LookupError(f"interval {name!r} (key={key}) not found on this vCenter")

    updated = vim.PerformanceManager.IntervalInfo(
        key=key,
        name=current.name,
        samplingPeriod=(interval_minutes * 60) if interval_minutes is not None else current.samplingPeriod,
        length=(save_days * 86400) if save_days is not None else current.length,
        level=level if level is not None else current.level,
        enabled=enabled if enabled is not None else current.enabled,
    )
    mgr.UpdatePerfInterval(interval=updated)
    return interval_get(opts, name, profile=profile)
