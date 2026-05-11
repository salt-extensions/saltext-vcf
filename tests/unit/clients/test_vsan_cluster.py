"""Tests for clients.vsan_cluster."""

from unittest.mock import MagicMock
from unittest.mock import patch

from saltext.vmware.clients import vsan_cluster


def _make_cluster_obj(enabled=True, auto_claim=False, uuid="vsan-uuid-1"):
    cluster = MagicMock()
    cluster._moId = "domain-c9"  # noqa: SLF001
    cluster.name = "mgmt-anchor"
    vsan_cfg = MagicMock()
    vsan_cfg.enabled = enabled
    vsan_cfg.defaultConfig.autoClaimStorage = auto_claim
    cluster.configurationEx.vsanConfigInfo = vsan_cfg
    return cluster


def test_get_basic_when_vsan_disabled(opts):
    cluster = _make_cluster_obj(enabled=False)
    with patch(
        "saltext.vmware.clients.vsan_cluster.vsan.find_cluster",
        return_value=cluster,
    ):
        with patch(
            "saltext.vmware.clients.vsan_cluster.vsan.cluster_config_system",
        ) as cs:
            cs.return_value.VsanClusterGetConfig.return_value = None
            result = vsan_cluster.get(opts, "domain-c9")
    assert result["enabled"] is False


def test_get_extended_when_vsan_enabled(opts):
    cluster = _make_cluster_obj(enabled=True, auto_claim=False)
    extended = MagicMock()
    extended.dataEfficiencyConfig.dedupEnabled = True
    extended.dataEncryptionConfig.encryptionEnabled = False
    extended.dataInTransitEncryptionConfig = None
    extended.vsanEsaEnabled = True

    with patch(
        "saltext.vmware.clients.vsan_cluster.vsan.find_cluster",
        return_value=cluster,
    ):
        with patch(
            "saltext.vmware.clients.vsan_cluster.vsan.cluster_config_system",
        ) as cs:
            cs.return_value.VsanClusterGetConfig.return_value = extended
            result = vsan_cluster.get(opts, "domain-c9")

    assert result["enabled"] is True
    assert result["dedup_compression_enabled"] is True
    assert result["encryption_enabled"] is False
    assert result["data_in_transit_encryption_enabled"] is False
    assert result["esa_enabled"] is True


def test_reconfigure_returns_task_id(opts):
    cluster = _make_cluster_obj()
    fake_task = MagicMock()
    fake_task._moId = "task-99"  # noqa: SLF001
    with patch(
        "saltext.vmware.clients.vsan_cluster.vsan.find_cluster",
        return_value=cluster,
    ):
        with patch(
            "saltext.vmware.clients.vsan_cluster.vsan.cluster_config_system",
        ) as cs:
            cs.return_value.VsanClusterReconfig.return_value = fake_task
            task_id = vsan_cluster.reconfigure(
                opts,
                "domain-c9",
                enabled=True,
                dedup_compression_enabled=True,
                auto_claim_storage=False,
            )
    assert task_id == "task-99"
    cs.return_value.VsanClusterReconfig.assert_called_once()


def test_runtime_info_returns_dict_or_empty(opts):
    cluster = _make_cluster_obj()
    runtime = MagicMock(totalCapacityB=100, freeCapacityB=40, usedCapacityB=60)
    with patch(
        "saltext.vmware.clients.vsan_cluster.vsan.find_cluster",
        return_value=cluster,
    ):
        with patch(
            "saltext.vmware.clients.vsan_cluster.vsan.cluster_config_system",
        ) as cs:
            cs.return_value.VsanClusterGetRuntimeStats.return_value = runtime
            result = vsan_cluster.runtime_info(opts, "domain-c9")
    assert result == {"capacity_total": 100, "capacity_free": 40, "capacity_used": 60}
