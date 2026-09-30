"""Tests for the vcf_vim_host_maintenance state module."""

import pytest

from saltext.vcf.clients import vim_host_maintenance as c
from saltext.vcf.states import vcf_vim_host_maintenance as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_already_in_maintenance(monkeypatch):
    monkeypatch.setattr(c, "is_in", lambda o, h, profile=None: True)
    ret = st.maintenance("mm", "esxi-01", enter_maintenance_mode=True)
    assert ret["changes"] == {}
    assert "already" in ret["comment"]


def test_enters_maintenance(monkeypatch):
    monkeypatch.setattr(c, "is_in", lambda o, h, profile=None: False)
    calls = []
    monkeypatch.setattr(c, "enter", lambda o, h, **kw: calls.append(kw))
    ret = st.maintenance("mm", "esxi-01", enter_maintenance_mode=True)
    assert ret["changes"] == {"maintenance": (False, True)}
    assert calls == [{"evacuate_powered_off_vms": False, "vsan_mode": None, "timeout": 0, "profile": None}]


def test_exits_maintenance(monkeypatch):
    monkeypatch.setattr(c, "is_in", lambda o, h, profile=None: True)
    calls = []
    monkeypatch.setattr(c, "exit_", lambda o, h, **kw: calls.append(kw))
    ret = st.maintenance("mm", "esxi-01", enter_maintenance_mode=False)
    assert ret["changes"] == {"maintenance": (True, False)}
    assert calls == [{"timeout": 0, "profile": None}]


def test_test_mode(monkeypatch):
    monkeypatch.setattr(c, "is_in", lambda o, h, profile=None: False)
    monkeypatch.setattr(c, "enter", lambda *a, **kw: pytest.fail("must not enter"))
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.maintenance("mm", "esxi-01", enter_maintenance_mode=True)
    assert ret["result"] is None
