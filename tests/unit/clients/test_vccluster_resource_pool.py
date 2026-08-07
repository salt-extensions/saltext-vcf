"""Tests for clients.vccluster_resource_pool (named child pool under a cluster)."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from saltext.vcf.clients import vccluster_resource_pool as c


def _cluster_with_pools(*pool_names):
    pools = []
    for n in pool_names:
        rp = MagicMock()
        rp.name = n
        rp._moId = f"rp-{n}"
        pools.append(rp)
    cluster = MagicMock()
    cluster.resourcePool.resourcePool = pools
    return cluster


def test_get_or_none_found(opts):
    cluster = _cluster_with_pools("Production")
    with patch("saltext.vcf.clients.vccluster_resource_pool._cluster", return_value=cluster):
        assert c.get_or_none(opts, "domain-c9", "Production") == "rp-Production"


def test_get_or_none_missing(opts):
    cluster = _cluster_with_pools()
    with patch("saltext.vcf.clients.vccluster_resource_pool._cluster", return_value=cluster):
        assert c.get_or_none(opts, "domain-c9", "Production") is None


def test_create_uses_cluster_root_pool_as_parent(opts):
    cluster = _cluster_with_pools()
    new_rp = MagicMock()
    new_rp._moId = "rp-new"
    cluster.resourcePool.CreateResourcePool.return_value = new_rp
    with patch("saltext.vcf.clients.vccluster_resource_pool._cluster", return_value=cluster):
        result = c.create(opts, "domain-c9", "Production")
    assert result == "rp-new"
    cluster.resourcePool.CreateResourcePool.assert_called_once()
    assert cluster.resourcePool.CreateResourcePool.call_args.kwargs["name"] == "Production"


def test_delete_calls_destroy(opts):
    cluster = _cluster_with_pools("Production")
    rp = cluster.resourcePool.resourcePool[0]
    task = MagicMock()
    rp.Destroy_Task.return_value = task
    with (
        patch("saltext.vcf.clients.vccluster_resource_pool._cluster", return_value=cluster),
        patch("saltext.vcf.clients.vccluster_resource_pool.soap.wait_for_task") as wait_mock,
    ):
        c.delete(opts, "domain-c9", "Production")
    rp.Destroy_Task.assert_called_once()
    wait_mock.assert_called_once_with(task)


def test_delete_missing_raises(opts):
    cluster = _cluster_with_pools()
    with patch("saltext.vcf.clients.vccluster_resource_pool._cluster", return_value=cluster):
        with pytest.raises(LookupError):
            c.delete(opts, "domain-c9", "Production")


def test_get_shares_missing_raises(opts):
    cluster = _cluster_with_pools()
    with patch("saltext.vcf.clients.vccluster_resource_pool._cluster", return_value=cluster):
        with pytest.raises(LookupError):
            c.get_shares(opts, "domain-c9", "Production")


def test_set_shares_delegates_to_vim_resource_pool(opts):
    cluster = _cluster_with_pools("Production")
    with (
        patch("saltext.vcf.clients.vccluster_resource_pool._cluster", return_value=cluster),
        patch("saltext.vcf.clients.vccluster_resource_pool.rp_c.set_shares") as set_shares_mock,
    ):
        c.set_shares(opts, "domain-c9", "Production", cpu={"shares_level": "high"})
    set_shares_mock.assert_called_once()
    assert set_shares_mock.call_args.args[1] == "rp-Production"
    assert set_shares_mock.call_args.kwargs["cpu"] == {"shares_level": "high"}
