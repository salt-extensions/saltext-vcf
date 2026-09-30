"""Tests for the vcf_vim_datastore state module."""

import pytest

from saltext.vcf.clients import vim_datastore as c
from saltext.vcf.states import vcf_vim_datastore as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_already_in_maintenance(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda o, n, profile=None: {"maintenance_mode": "inMaintenance"})
    ret = st.maintenance_mode("ds1", enter_maintenance_mode=True)
    assert ret["changes"] == {}


def test_enters_maintenance(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda o, n, profile=None: {"maintenance_mode": "normal"})
    called = []
    monkeypatch.setattr(c, "enter_maintenance", lambda o, n, profile=None: called.append(n))
    ret = st.maintenance_mode("ds1", enter_maintenance_mode=True)
    assert ret["changes"] == {"maintenance": (False, True)}
    assert called == ["ds1"]


def test_exits_maintenance(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda o, n, profile=None: {"maintenance_mode": "inMaintenance"})
    called = []
    monkeypatch.setattr(c, "exit_maintenance", lambda o, n, profile=None: called.append(n))
    ret = st.maintenance_mode("ds1", enter_maintenance_mode=False)
    assert ret["changes"] == {"maintenance": (True, False)}


def test_missing_datastore_fails(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda o, n, profile=None: None)
    ret = st.maintenance_mode("nope")
    assert ret["result"] is False
