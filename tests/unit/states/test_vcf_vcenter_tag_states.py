"""Tests for the vcf_vcenter_tag / vcf_vcenter_tag_category state modules."""

import pytest

from saltext.vcf.clients import vcenter_tag as tag_c
from saltext.vcf.clients import vcenter_tag_category as cat_c
from saltext.vcf.states import vcf_vcenter_tag as tag_st
from saltext.vcf.states import vcf_vcenter_tag_category as cat_st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(tag_st, "__opts__", opts, raising=False)
    monkeypatch.setattr(cat_st, "__opts__", opts, raising=False)


# ---------- tag category ----------


def test_category_present_creates(monkeypatch):
    monkeypatch.setattr(cat_c, "by_name", lambda o, n, profile=None: None)
    called = {}
    monkeypatch.setattr(
        cat_c,
        "create",
        lambda o, n, **kw: called.update(name=n, **kw),
    )
    ret = cat_st.present("environment", cardinality="MULTIPLE", associable_types=["VirtualMachine"])
    assert ret["changes"] == {"new": "environment"}
    assert called["cardinality"] == "MULTIPLE"


def test_category_present_updates_on_drift(monkeypatch):
    monkeypatch.setattr(
        cat_c,
        "by_name",
        lambda o, n, profile=None: {"id": "urn:cat", "name": n, "cardinality": "SINGLE",
                                    "description": "old", "associable_types": ["VirtualMachine"]},
    )
    monkeypatch.setattr(cat_c, "update", lambda o, cid, spec, profile=None: None)
    ret = cat_st.present("environment", description="new")
    assert ret["changes"]["description"] == ("old", "new")


def test_category_present_noop(monkeypatch):
    monkeypatch.setattr(
        cat_c,
        "by_name",
        lambda o, n, profile=None: {"id": "urn:cat", "name": n, "cardinality": "SINGLE",
                                    "description": "", "associable_types": ["VirtualMachine"]},
    )
    ret = cat_st.present("environment", cardinality="SINGLE", associable_types=["VirtualMachine"])
    assert ret["changes"] == {}


def test_category_absent(monkeypatch):
    monkeypatch.setattr(
        cat_c, "by_name", lambda o, n, profile=None: {"id": "urn:cat", "name": n}
    )
    monkeypatch.setattr(cat_c, "delete", lambda o, cid, profile=None: None)
    ret = cat_st.absent("environment")
    assert ret["changes"] == {"old": "environment"}


# ---------- tag ----------


def test_tag_present_creates(monkeypatch):
    monkeypatch.setattr(cat_c, "by_name", lambda o, n, profile=None: {"id": "urn:cat", "name": n})
    monkeypatch.setattr(tag_c, "list_", lambda o, profile=None: [])
    called = {}
    monkeypatch.setattr(
        tag_c, "create", lambda o, n, cid, description="", profile=None: called.update(name=n, cid=cid)
    )
    ret = tag_st.present("env-prod", category="environment", description="production")
    assert ret["changes"] == {"new": "env-prod"}
    assert called == {"name": "env-prod", "cid": "urn:cat"}


def test_tag_present_updates_description(monkeypatch):
    monkeypatch.setattr(cat_c, "by_name", lambda o, n, profile=None: {"id": "urn:cat", "name": n})
    monkeypatch.setattr(
        tag_c, "list_", lambda o, profile=None: [{"id": "urn:tag", "name": "env-prod"}]
    )
    monkeypatch.setattr(
        tag_c,
        "get",
        lambda o, t, profile=None: {"id": "urn:tag", "name": "env-prod", "category_id": "urn:cat", "description": "old"},
    )
    monkeypatch.setattr(tag_c, "update", lambda o, t, spec, profile=None: None)
    ret = tag_st.present("env-prod", category="environment", description="new")
    assert ret["changes"] == {"description": ("old", "new")}


def test_tag_present_unknown_category(monkeypatch):
    monkeypatch.setattr(cat_c, "by_name", lambda o, n, profile=None: None)
    monkeypatch.setattr(cat_c, "get_or_none", lambda o, c, profile=None: None)
    monkeypatch.setattr(tag_c, "list_", lambda o, profile=None: [])
    monkeypatch.setattr(
        tag_c, "create", lambda *a, **kw: pytest.fail("must not create for unknown category")
    )
    ret = tag_st.present("env-prod", category="missing")
    assert ret["result"] is False


def test_tag_absent(monkeypatch):
    monkeypatch.setattr(
        tag_c, "list_", lambda o, profile=None: [{"id": "urn:tag", "name": "env-prod"}]
    )
    monkeypatch.setattr(tag_c, "delete", lambda o, t, profile=None: None)
    ret = tag_st.absent("env-prod")
    assert ret["changes"] == {"old": "env-prod"}


def test_tag_absent_noop(monkeypatch):
    monkeypatch.setattr(tag_c, "list_", lambda o, profile=None: [])
    ret = tag_st.absent("env-prod")
    assert ret["changes"] == {}
