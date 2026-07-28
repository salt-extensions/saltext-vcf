"""Tests for states.vcf_vcenter_dvs_nioc_vccluster."""

import pytest

from saltext.vcf.clients import vcenter_dvs_nioc_vccluster as c
from saltext.vcf.states import vcf_vcenter_dvs_nioc_vccluster as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_nioc_already_matches(monkeypatch):
    monkeypatch.setattr(
        c, "nioc_get", lambda opts, cluster, profile=None: {"dvs-1": True, "dvs-2": True}
    )
    ret = st.nioc_enabled("cluster-1", enabled=True)
    assert ret["changes"] == {}


def test_nioc_enables_drifted_only(monkeypatch):
    calls = []
    monkeypatch.setattr(
        c, "nioc_get", lambda opts, cluster, profile=None: {"dvs-1": False, "dvs-2": True}
    )
    monkeypatch.setattr(
        c, "nioc_set", lambda opts, cluster, enabled, profile=None: calls.append((cluster, enabled))
    )
    ret = st.nioc_enabled("cluster-1", enabled=True)
    assert ret["changes"] == {"dvs-1": {"old": False, "new": True}}
    assert calls == [("cluster-1", True)]


def test_nioc_test_mode(monkeypatch):
    monkeypatch.setattr(c, "nioc_get", lambda opts, cluster, profile=None: {"dvs-1": False})
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.nioc_enabled("cluster-1", enabled=True)
    assert ret["result"] is None
