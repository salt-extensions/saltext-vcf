"""vCenter PerfManager (SOAP) — historical performance counter queries.

REST `/api/stats/` exists but is limited to monitor/policy management,
not raw counter retrieval with sampling intervals. PerfManager is the only
path for things like "give me VM CPU usage every 20 seconds for the past
hour" or "summarize cluster memory consumption by month".
"""

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from pyVmomi import vim

from saltext.vmware.utils import vim as soap


def counters(opts, profile=None):
    """Return all counters defined on vCenter, as a dict keyed by counter id.

    Each entry includes ``group``, ``name``, ``unit``, ``rollup_type``,
    ``stats_type``. Useful as a discovery step before calling :func:`query`.
    """
    pm = soap.perf_manager(opts, profile=profile)
    return {
        c.key: {
            "group": c.groupInfo.key,
            "name": c.nameInfo.key,
            "unit": c.unitInfo.key,
            "rollup_type": str(c.rollupType),
            "stats_type": str(c.statsType),
            "level": c.level,
        }
        for c in pm.perfCounter
    }


def available_metrics(opts, entity_mo_id, entity_type=None, profile=None):
    """List the perf metrics available for a given managed entity.

    *entity_mo_id* is the MoId (e.g. ``vm-12``, ``host-9``). *entity_type*
    is the pyVmomi class name (e.g. ``VirtualMachine``); inferred from the
    MoId prefix when omitted.
    """
    si = soap.get_service_instance(opts, profile=profile)
    pm = soap.perf_manager(opts, profile=profile)
    entity = _resolve_entity(si, entity_mo_id, entity_type)
    metrics = pm.QueryAvailablePerfMetric(entity=entity)
    return [{"counter_id": m.counterId, "instance": m.instance} for m in metrics]


def query(
    opts,
    entity_mo_id,
    counter_ids,
    *,
    entity_type=None,
    interval_id=20,
    start_time=None,
    end_time=None,
    max_samples=None,
    profile=None,
):
    """Query perf counters for *entity_mo_id*.

    *counter_ids* is a list of counter integer keys (from :func:`counters`).
    *interval_id* is the historical interval (20 = real-time on most envs,
    or one of 300/1800/7200/86400 for aggregated rollups).
    *start_time* / *end_time* are :class:`datetime.datetime` (UTC). If
    *start_time* is omitted and *max_samples* is also omitted, defaults
    to the last 10 samples.
    """
    si = soap.get_service_instance(opts, profile=profile)
    pm = soap.perf_manager(opts, profile=profile)
    entity = _resolve_entity(si, entity_mo_id, entity_type)
    metric_ids = [vim.PerformanceManager.MetricId(counterId=c, instance="*") for c in counter_ids]
    spec = vim.PerformanceManager.QuerySpec(
        entity=entity,
        metricId=metric_ids,
        intervalId=interval_id,
        startTime=start_time,
        endTime=end_time,
        maxSample=(max_samples if max_samples is not None else (None if start_time else 10)),
    )
    return [_query_result_to_dict(r) for r in pm.QueryPerf(querySpec=[spec])]


def last_n_seconds(opts, entity_mo_id, counter_ids, seconds=300, **kwargs):
    """Convenience: query the last *seconds* of perf data."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(seconds=seconds)
    return query(opts, entity_mo_id, counter_ids, start_time=start, end_time=end, **kwargs)


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------


def _resolve_entity(si, mo_id, entity_type):
    """Resolve a MoId+type into a pyVmomi managed object reference."""
    type_map = {
        "VirtualMachine": vim.VirtualMachine,
        "HostSystem": vim.HostSystem,
        "ClusterComputeResource": vim.ClusterComputeResource,
        "Datastore": vim.Datastore,
        "Datacenter": vim.Datacenter,
        "ResourcePool": vim.ResourcePool,
    }
    if entity_type is None:
        prefix = mo_id.split("-")[0] if "-" in mo_id else mo_id
        # Heuristic mapping by MoId prefix
        prefix_map = {
            "vm": "VirtualMachine",
            "host": "HostSystem",
            "domain": "ClusterComputeResource",
            "datastore": "Datastore",
            "datacenter": "Datacenter",
            "resgroup": "ResourcePool",
        }
        entity_type = prefix_map.get(prefix, "VirtualMachine")
    cls = type_map.get(entity_type, vim.ManagedEntity)
    return cls(mo_id, si._stub)


def _query_result_to_dict(result):
    sample_info = getattr(result, "sampleInfo", None) or []
    return {
        "entity": result.entity._moId,
        "sample_times": [s.timestamp.isoformat() for s in sample_info],
        "interval_seconds": [s.interval for s in sample_info],
        "values": [
            {
                "counter_id": v.id.counterId,
                "instance": v.id.instance,
                "values": list(v.value),
            }
            for v in (getattr(result, "value", None) or [])
        ],
    }
