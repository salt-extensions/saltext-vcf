"""Tests for states.vcf_vcenter_ad_domain."""

import pytest

from saltext.vcf.clients import vcenter_ad_domain as c
from saltext.vcf.states import vcf_vcenter_ad_domain as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_ad_joined_already(monkeypatch):
    monkeypatch.setattr(
        c,
        "get",
        lambda opts, domain_name, profile=None: {
            "provider": "p-1",
            "config_tag": "ActiveDirectory",
            "domain_name": domain_name,
        },
    )
    ret = st.ad_joined("corp.example", username="admin", password="secret")
    assert ret["changes"] == {}


def test_ad_joined_joins(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "get", lambda opts, domain_name, profile=None: None)
    monkeypatch.setattr(
        c,
        "join",
        lambda opts, domain_name, username, password, profile=None: calls.append(
            (domain_name, username, password)
        )
        or "p-99",
    )
    ret = st.ad_joined("corp.example", username="admin", password="secret")
    assert ret["changes"] == {"new": "p-99"}
    assert calls == [("corp.example", "admin", "secret")]


def test_ad_joined_test_mode(monkeypatch):
    monkeypatch.setattr(c, "get", lambda opts, domain_name, profile=None: None)
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.ad_joined("corp.example", username="admin", password="secret")
    assert ret["result"] is None


def test_ad_absent_already(monkeypatch):
    monkeypatch.setattr(c, "get", lambda opts, domain_name, profile=None: None)
    ret = st.ad_absent("corp.example")
    assert ret["changes"] == {}


def test_ad_absent_leaves(monkeypatch):
    calls = []
    monkeypatch.setattr(
        c,
        "get",
        lambda opts, domain_name, profile=None: {
            "provider": "p-1",
            "config_tag": "ActiveDirectory",
            "domain_name": domain_name,
        },
    )
    monkeypatch.setattr(
        c, "leave", lambda opts, provider_id, profile=None: calls.append(provider_id)
    )
    ret = st.ad_absent("corp.example")
    assert ret["changes"] == {"deleted": "corp.example"}
    assert calls == ["p-1"]


def test_ad_absent_test_mode(monkeypatch):
    monkeypatch.setattr(
        c,
        "get",
        lambda opts, domain_name, profile=None: {
            "provider": "p-1",
            "config_tag": "ActiveDirectory",
            "domain_name": domain_name,
        },
    )
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.ad_absent("corp.example")
    assert ret["result"] is None
