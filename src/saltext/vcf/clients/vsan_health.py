"""vSAN cluster health checks (SOAP via /vsanHealth)."""

from pyVmomi import vim
from pyVmomi import vmodl  # pylint: disable=no-name-in-module

from saltext.vcf.utils import vsan


def summary(opts, cluster, *, fetch_from_cache=True, profile=None):
    """Return the vSAN health-test summary for *cluster*.

    The summary aggregates ~100 health tests into a single dict with
    overall health string and a list of group results.
    """
    cluster_obj = vsan.find_cluster(opts, cluster, profile=profile)
    hs = vsan.cluster_health_system(opts, profile=profile)
    try:
        # pyVmomi vmodl methods carry many optional args that pylint sees as required.
        result = hs.QueryClusterHealthSummary(  # pylint: disable=no-value-for-parameter
            cluster=cluster_obj,
            fetchFromCache=fetch_from_cache,
        )
    except vim.fault.VimFault as exc:
        return {"error": str(exc)}

    return _summary_to_dict(result)


def groups(opts, cluster, *, fetch_from_cache=True, profile=None):
    """Return health-test groups as a flat list of dicts.

    Each entry: ``{"group_id", "group_name", "health", "tests": [...]}``.
    """
    summary_dict = summary(opts, cluster, fetch_from_cache=fetch_from_cache, profile=profile)
    return summary_dict.get("groups", [])


def overall(opts, cluster, *, fetch_from_cache=True, profile=None):
    """Return only the overall health string (e.g. ``"green"``, ``"yellow"``, ``"red"``)."""
    summary_dict = summary(opts, cluster, fetch_from_cache=fetch_from_cache, profile=profile)
    return summary_dict.get("overall_health")


def silenced_checks(opts, cluster, profile=None):
    """List health tests currently silenced (suppressed from overall health)."""
    cluster_obj = vsan.find_cluster(opts, cluster, profile=profile)
    hs = vsan.cluster_health_system(opts, profile=profile)
    try:
        return list(hs.GetVsanClusterSilentChecks(cluster=cluster_obj) or [])
    except (vim.fault.VimFault, vmodl.MethodFault, AttributeError):
        return []


def silence(opts, cluster, checks, profile=None):
    """Silence a list of health-test ids on *cluster*."""
    cluster_obj = vsan.find_cluster(opts, cluster, profile=profile)
    hs = vsan.cluster_health_system(opts, profile=profile)
    # pylint: disable=no-value-for-parameter
    hs.SetVsanClusterSilentChecks(cluster=cluster_obj, addSilentChecks=list(checks))


def unsilence(opts, cluster, checks, profile=None):
    """Re-enable silenced health-test ids on *cluster*."""
    cluster_obj = vsan.find_cluster(opts, cluster, profile=profile)
    hs = vsan.cluster_health_system(opts, profile=profile)
    # pylint: disable=no-value-for-parameter
    hs.SetVsanClusterSilentChecks(cluster=cluster_obj, removeSilentChecks=list(checks))


def _summary_to_dict(result):
    """Project a VsanClusterHealthSummary into plain dicts."""
    overall_status = getattr(result, "overallHealth", None)
    out = {
        "overall_health": overall_status,
        "overall_health_description": getattr(result, "overallHealthDescription", None),
        "groups": [],
    }
    for group in getattr(result, "groups", None) or []:
        tests = []
        for test in getattr(group, "groupTests", None) or []:
            tests.append(
                {
                    "id": getattr(test, "testId", None),
                    "name": getattr(test, "testName", None),
                    "health": getattr(test, "testHealth", None),
                    "description": getattr(test, "testShortDescription", None),
                }
            )
        out["groups"].append(
            {
                "group_id": getattr(group, "groupId", None),
                "group_name": getattr(group, "groupName", None),
                "group_health": getattr(group, "groupHealth", None),
                "tests": tests,
            }
        )
    return out
