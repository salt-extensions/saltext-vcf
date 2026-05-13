"""Tests for clients.vim_cluster_evc."""

from unittest.mock import MagicMock

import pytest

from saltext.vmware.clients import vim_cluster_evc


@pytest.fixture
def cluster_factory(monkeypatch):
    cl = MagicMock()
    mgr = MagicMock()
    mgr.evcState.currentEVCModeKey = "intel-sandybridge"
    mode_a = MagicMock(key="intel-sandybridge")
    mode_b = MagicMock(key="intel-haswell")
    mgr.evcState.supportedEVCMode = [mode_a, mode_b]
    mgr.evcState.guaranteedCPUFeatures = []
    mgr.ConfigureEvcMode_Task.return_value = MagicMock(_moId="task-evc-cfg")
    mgr.DisableEvcMode_Task.return_value = MagicMock(_moId="task-evc-off")
    mgr.CheckConfigureEvcMode_Task.return_value = MagicMock(_moId="task-evc-check")
    cl.EvcManager.return_value = mgr
    monkeypatch.setattr(vim_cluster_evc, "_cluster", lambda o, n, profile=None: cl)
    return {"cl": cl, "mgr": mgr}


def test_get(opts, cluster_factory):
    out = vim_cluster_evc.get(opts, "domain-c9")
    assert out["enabled"] is True
    assert out["current_key"] == "intel-sandybridge"
    assert "intel-haswell" in out["supported_keys"]


def test_configure(opts, cluster_factory):
    assert vim_cluster_evc.configure(opts, "domain-c9", "intel-haswell") == "task-evc-cfg"
    cluster_factory["mgr"].ConfigureEvcMode_Task.assert_called_with(evcModeKey="intel-haswell")


def test_disable(opts, cluster_factory):
    assert vim_cluster_evc.disable(opts, "domain-c9") == "task-evc-off"


def test_check(opts, cluster_factory):
    assert vim_cluster_evc.check(opts, "domain-c9", "intel-haswell") == "task-evc-check"


def test_no_evc_manager(opts, monkeypatch):
    cl = MagicMock()
    cl.name = "domain-c9"
    cl.EvcManager.return_value = None
    monkeypatch.setattr(vim_cluster_evc, "_cluster", lambda o, n, profile=None: cl)
    with pytest.raises(RuntimeError, match="EVC manager"):
        vim_cluster_evc.get(opts, "domain-c9")
