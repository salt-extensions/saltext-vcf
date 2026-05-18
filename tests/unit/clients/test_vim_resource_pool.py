"""Tests for clients.vim_resource_pool (SOAP move + shares)."""

from unittest.mock import MagicMock

import pytest

from saltext.vcf.clients import vim_resource_pool


def _make_rp(mo_id="rp-1", name="Resources"):
    rp = MagicMock()
    rp._moId = mo_id  # noqa: SLF001
    rp.name = name
    cfg = MagicMock()
    cfg.cpuAllocation.reservation = 0
    cfg.cpuAllocation.expandableReservation = True
    cfg.cpuAllocation.limit = -1
    cfg.cpuAllocation.shares.level = "normal"
    cfg.cpuAllocation.shares.shares = 4000
    cfg.memoryAllocation.reservation = 0
    cfg.memoryAllocation.expandableReservation = True
    cfg.memoryAllocation.limit = -1
    cfg.memoryAllocation.shares.level = "normal"
    cfg.memoryAllocation.shares.shares = 163840
    rp.config = cfg
    return rp


@pytest.fixture
def rp_lookup(monkeypatch):
    rps = {"rp-1": _make_rp("rp-1", "Resources"), "rp-2": _make_rp("rp-2", "Child")}

    def fake_find(opts, name, profile=None):
        if name in rps:
            return rps[name]
        raise LookupError(name)

    monkeypatch.setattr(vim_resource_pool, "_find_rp", fake_find)
    return rps


def test_move_into_target(opts, rp_lookup):
    out = vim_resource_pool.move(opts, "rp-2", "rp-1")
    assert out == {"resource_pool": "rp-2", "new_parent": "rp-1"}
    rp_lookup["rp-1"].MoveIntoResourcePool.assert_called_once()
    call = rp_lookup["rp-1"].MoveIntoResourcePool.call_args
    assert call.kwargs["list"] == [rp_lookup["rp-2"]]


def test_get_shares(opts, rp_lookup):
    out = vim_resource_pool.get_shares(opts, "rp-1")
    assert out["cpu"]["shares_level"] == "normal"
    assert out["cpu"]["shares_value"] == 4000
    assert out["memory"]["limit"] == -1


def test_set_shares_writes_config(opts, rp_lookup):
    out = vim_resource_pool.set_shares(
        opts,
        "rp-1",
        cpu={"shares_level": "high"},
        memory={"reservation": 1024, "limit": 4096},
    )
    rp_lookup["rp-1"].UpdateConfig.assert_called_once()
    spec = rp_lookup["rp-1"].UpdateConfig.call_args.kwargs["config"]
    assert spec.cpuAllocation.shares.level == "high"
    assert spec.memoryAllocation.reservation == 1024
    assert spec.memoryAllocation.limit == 4096
    # get_shares returned the lookup's cached state
    assert "cpu" in out and "memory" in out
