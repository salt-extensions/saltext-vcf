"""Tests for clients.vsan_health."""

from unittest.mock import MagicMock
from unittest.mock import patch

from saltext.vmware.clients import vsan_health


def _make_summary():
    summary = MagicMock()
    summary.overallHealth = "green"
    summary.overallHealthDescription = "All tests passed"

    test1 = MagicMock(
        testId="t1",
        testName="Cluster status",
        testHealth="green",
        testShortDescription="ok",
    )
    test2 = MagicMock(
        testId="t2", testName="Network", testHealth="green", testShortDescription="ok"
    )

    group = MagicMock(
        groupId="g1",
        groupName="Cluster",
        groupHealth="green",
        groupTests=[test1, test2],
    )
    summary.groups = [group]
    return summary


def test_summary_returns_projection(opts):
    cluster = MagicMock()
    summary = _make_summary()
    with patch(
        "saltext.vmware.clients.vsan_health.vsan.find_cluster",
        return_value=cluster,
    ):
        with patch(
            "saltext.vmware.clients.vsan_health.vsan.cluster_health_system",
        ) as hs:
            hs.return_value.QueryClusterHealthSummary.return_value = summary
            out = vsan_health.summary(opts, "domain-c9")

    assert out["overall_health"] == "green"
    assert out["overall_health_description"] == "All tests passed"
    assert out["groups"][0]["group_id"] == "g1"
    assert len(out["groups"][0]["tests"]) == 2


def test_overall_returns_string(opts):
    cluster = MagicMock()
    with patch(
        "saltext.vmware.clients.vsan_health.vsan.find_cluster",
        return_value=cluster,
    ):
        with patch(
            "saltext.vmware.clients.vsan_health.vsan.cluster_health_system",
        ) as hs:
            hs.return_value.QueryClusterHealthSummary.return_value = _make_summary()
            assert vsan_health.overall(opts, "domain-c9") == "green"


def test_silenced_checks_returns_list(opts):
    cluster = MagicMock()
    with patch(
        "saltext.vmware.clients.vsan_health.vsan.find_cluster",
        return_value=cluster,
    ):
        with patch(
            "saltext.vmware.clients.vsan_health.vsan.cluster_health_system",
        ) as hs:
            hs.return_value.GetVsanClusterSilentChecks.return_value = ["t1", "t2"]
            assert vsan_health.silenced_checks(opts, "domain-c9") == ["t1", "t2"]


def test_silence_calls_setvsanclustersilentchecks(opts):
    cluster = MagicMock()
    with patch(
        "saltext.vmware.clients.vsan_health.vsan.find_cluster",
        return_value=cluster,
    ):
        with patch(
            "saltext.vmware.clients.vsan_health.vsan.cluster_health_system",
        ) as hs:
            vsan_health.silence(opts, "domain-c9", ["t1"])
            hs.return_value.SetVsanClusterSilentChecks.assert_called_once_with(
                cluster=cluster, addSilentChecks=["t1"]
            )
