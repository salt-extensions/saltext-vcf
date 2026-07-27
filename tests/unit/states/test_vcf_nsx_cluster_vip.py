"""Tests for the vcf_nsx_cluster_vip state module."""

from saltext.vcf.states import vcf_nsx_cluster_vip


def _no_test(monkeypatch):
    monkeypatch.setattr(vcf_nsx_cluster_vip, "__opts__", {"test": False}, raising=False)


def _test_mode(monkeypatch):
    monkeypatch.setattr(vcf_nsx_cluster_vip, "__opts__", {"test": True}, raising=False)


def test_api_vip_set_noops_when_already_matching(monkeypatch):
    _no_test(monkeypatch)
    monkeypatch.setattr(
        vcf_nsx_cluster_vip.c,
        "api_virtual_ip_get",
        lambda opts, profile=None: {"ip_address": "10.0.0.5"},
    )

    def _fail(*a, **kw):
        raise AssertionError("should not call set when matching")

    monkeypatch.setattr(vcf_nsx_cluster_vip.c, "api_virtual_ip_set", _fail)

    ret = vcf_nsx_cluster_vip.api_vip_set("cluster-vip", ip_address="10.0.0.5")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert "already" in ret["comment"]


def test_api_vip_set_applies_change(monkeypatch):
    _no_test(monkeypatch)
    monkeypatch.setattr(
        vcf_nsx_cluster_vip.c,
        "api_virtual_ip_get",
        lambda opts, profile=None: {"ip_address": ""},
    )
    calls = {}

    def _set(opts, ip, profile=None):
        calls["ip"] = ip
        return {"ip_address": ip}

    monkeypatch.setattr(vcf_nsx_cluster_vip.c, "api_virtual_ip_set", _set)

    ret = vcf_nsx_cluster_vip.api_vip_set("cluster-vip", ip_address="10.0.0.5")
    assert ret["result"] is True
    assert ret["changes"] == {"old": "", "new": "10.0.0.5"}
    assert calls["ip"] == "10.0.0.5"


def test_api_vip_set_uses_name_when_ip_omitted(monkeypatch):
    _no_test(monkeypatch)
    monkeypatch.setattr(
        vcf_nsx_cluster_vip.c,
        "api_virtual_ip_get",
        lambda opts, profile=None: {"ip_address": ""},
    )
    calls = {}
    monkeypatch.setattr(
        vcf_nsx_cluster_vip.c,
        "api_virtual_ip_set",
        lambda opts, ip, profile=None: calls.setdefault("ip", ip),
    )
    ret = vcf_nsx_cluster_vip.api_vip_set("10.0.0.5")
    assert ret["changes"] == {"old": "", "new": "10.0.0.5"}
    assert calls["ip"] == "10.0.0.5"


def test_api_vip_set_test_mode(monkeypatch):
    _test_mode(monkeypatch)
    monkeypatch.setattr(
        vcf_nsx_cluster_vip.c,
        "api_virtual_ip_get",
        lambda opts, profile=None: {"ip_address": "10.0.0.4"},
    )

    def _fail(*a, **kw):
        raise AssertionError("must not call set in test mode")

    monkeypatch.setattr(vcf_nsx_cluster_vip.c, "api_virtual_ip_set", _fail)
    ret = vcf_nsx_cluster_vip.api_vip_set("cluster-vip", ip_address="10.0.0.5")
    assert ret["result"] is None
    assert ret["changes"] == {"old": "10.0.0.4", "new": "10.0.0.5"}


def test_api_vip_absent_noops_when_cleared(monkeypatch):
    _no_test(monkeypatch)
    monkeypatch.setattr(
        vcf_nsx_cluster_vip.c,
        "api_virtual_ip_get",
        lambda opts, profile=None: {"ip_address": ""},
    )

    def _fail(*a, **kw):
        raise AssertionError("must not call clear when already cleared")

    monkeypatch.setattr(vcf_nsx_cluster_vip.c, "api_virtual_ip_clear", _fail)
    ret = vcf_nsx_cluster_vip.api_vip_absent("cluster-vip")
    assert ret["result"] is True
    assert ret["changes"] == {}


def test_api_vip_absent_clears(monkeypatch):
    _no_test(monkeypatch)
    monkeypatch.setattr(
        vcf_nsx_cluster_vip.c,
        "api_virtual_ip_get",
        lambda opts, profile=None: {"ip_address": "10.0.0.5"},
    )
    called = {}
    monkeypatch.setattr(
        vcf_nsx_cluster_vip.c,
        "api_virtual_ip_clear",
        lambda opts, profile=None: called.setdefault("called", True),
    )
    ret = vcf_nsx_cluster_vip.api_vip_absent("cluster-vip")
    assert ret["result"] is True
    assert ret["changes"] == {"old": "10.0.0.5", "new": ""}
    assert called["called"]


def test_api_vip_absent_test_mode(monkeypatch):
    _test_mode(monkeypatch)
    monkeypatch.setattr(
        vcf_nsx_cluster_vip.c,
        "api_virtual_ip_get",
        lambda opts, profile=None: {"ip_address": "10.0.0.5"},
    )

    def _fail(*a, **kw):
        raise AssertionError("must not call clear in test mode")

    monkeypatch.setattr(vcf_nsx_cluster_vip.c, "api_virtual_ip_clear", _fail)
    ret = vcf_nsx_cluster_vip.api_vip_absent("cluster-vip")
    assert ret["result"] is None
    assert ret["changes"] == {"old": "10.0.0.5", "new": ""}
