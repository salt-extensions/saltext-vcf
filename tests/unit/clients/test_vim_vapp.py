"""Tests for clients.vim_vapp."""

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vcf.clients import vim_vapp


def _make_vapp(mo_id="vapp-1", name="prod"):
    v = MagicMock()
    v._moId = mo_id  # noqa: SLF001
    v.name = name
    v.parent._moId = "rp-1"  # noqa: SLF001
    v.summary.overallStatus = "green"
    v.vm = []
    v.vAppConfig.annotation = "test annotation"
    v.vAppConfig.product = []
    v.PowerOnVApp_Task.return_value = MagicMock(_moId="task-on")
    v.PowerOffVApp_Task.return_value = MagicMock(_moId="task-off")
    v.SuspendVApp_Task.return_value = MagicMock(_moId="task-susp")
    v.Destroy_Task.return_value = MagicMock(_moId="task-del")
    return v


@pytest.fixture
def env(monkeypatch):
    v = _make_vapp()
    rp = vim.ResourcePool("rp-1", None)
    monkeypatch.setattr(vim_vapp, "_find_vapp", lambda o, n, profile=None: v)
    monkeypatch.setattr(vim_vapp, "_find_resource_pool", lambda o, n, profile=None: rp)
    return {"vapp": v, "rp": rp}


def test_get_returns_dict(opts, env):
    out = vim_vapp.get(opts, "prod")
    assert out["id"] == "vapp-1"
    assert out["annotation"] == "test annotation"


def test_get_or_none_missing(opts, monkeypatch):
    monkeypatch.setattr(
        vim_vapp,
        "_find_vapp",
        lambda o, n, profile=None: (_ for _ in ()).throw(LookupError("missing")),
    )
    assert vim_vapp.get_or_none(opts, "missing") is None


def test_power_on_off_suspend_delete(opts, env):
    assert vim_vapp.power_on(opts, "prod") == "task-on"
    assert vim_vapp.power_off(opts, "prod") == "task-off"
    env["vapp"].PowerOffVApp_Task.assert_called_with(force=False)
    assert vim_vapp.suspend(opts, "prod") == "task-susp"
    assert vim_vapp.delete(opts, "prod") == "task-del"


def test_update_sets_annotation(opts, env):
    vim_vapp.update(opts, "prod", annotation="new")
    env["vapp"].UpdateVAppConfig.assert_called_once()
    spec = env["vapp"].UpdateVAppConfig.call_args.kwargs["spec"]
    assert spec.annotation == "new"


def test_create_uses_resource_pool(opts, env, monkeypatch):
    # Mock the resource pool's CreateVApp to return our fake vapp
    rp_mock = MagicMock()
    rp_mock.CreateVApp.return_value = env["vapp"]
    monkeypatch.setattr(vim_vapp, "_find_resource_pool", lambda o, n, profile=None: rp_mock)
    out = vim_vapp.create(opts, "newapp", "rp-1", annotation="hi")
    assert out["id"] == "vapp-1"
    rp_mock.CreateVApp.assert_called_once()
