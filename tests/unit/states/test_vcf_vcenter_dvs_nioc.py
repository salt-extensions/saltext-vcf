"""Tests for states.vcf_vcenter_dvs_nioc."""

import pytest

from saltext.vcf.clients import vcenter_dvs_nioc as c
from saltext.vcf.states import vcf_vcenter_dvs_nioc as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_nioc_already_matches(monkeypatch):
    monkeypatch.setattr(c, "nioc_get", lambda opts, dvs, profile=None: True)
    ret = st.nioc_enabled("dvs-1", enabled=True)
    assert ret["changes"] == {}


def test_nioc_enables(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "nioc_get", lambda opts, dvs, profile=None: False)
    monkeypatch.setattr(
        c, "nioc_set", lambda opts, dvs, enabled, profile=None: calls.append((dvs, enabled))
    )
    ret = st.nioc_enabled("dvs-1", enabled=True)
    assert ret["changes"] == {"enabled": {"old": False, "new": True}}
    assert calls == [("dvs-1", True)]


def test_nioc_test_mode(monkeypatch):
    monkeypatch.setattr(c, "nioc_get", lambda opts, dvs, profile=None: False)
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.nioc_enabled("dvs-1", enabled=True)
    assert ret["result"] is None
