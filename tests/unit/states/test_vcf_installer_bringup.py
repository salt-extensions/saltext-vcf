"""Tests for the VCF Installer bringup state module."""

import pytest

from saltext.vcf.clients import installer_bringup as c
from saltext.vcf.states import vcf_installer_bringup as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_validated_returns_success(monkeypatch):
    monkeypatch.setattr(c, "validate", lambda o, s, profile=None: {"id": "val-1"})
    monkeypatch.setattr(
        c,
        "wait_validation",
        lambda o, vid, timeout=None, profile=None: {"resultStatus": "SUCCEEDED"},
    )
    ret = st.validated("validate-mgmt-spec", spec={"any": "spec"})
    assert ret["result"] is True
    assert ret["changes"] == {"validation_id": "val-1"}


def test_validated_no_wait(monkeypatch):
    monkeypatch.setattr(c, "validate", lambda o, s, profile=None: {"id": "val-1"})
    monkeypatch.setattr(c, "wait_validation", lambda *a, **kw: pytest.fail("should not wait"))
    ret = st.validated("name", spec={}, wait=False)
    assert "submitted" in ret["comment"]


def test_validated_failure(monkeypatch):
    monkeypatch.setattr(c, "validate", lambda o, s, profile=None: {"id": "val-1"})

    def fail(*a, **kw):
        raise RuntimeError("bad spec")

    monkeypatch.setattr(c, "wait_validation", fail)
    ret = st.validated("name", spec={})
    assert ret["result"] is False
    assert "bad spec" in ret["comment"]


def test_complete_idempotent_when_bringup_done(monkeypatch):
    monkeypatch.setattr(
        c, "list_", lambda o, profile=None: [{"id": "sddc-1", "status": "COMPLETED_WITH_SUCCESS"}]
    )
    monkeypatch.setattr(c, "submit", lambda *a, **kw: pytest.fail("should not submit"))
    ret = st.complete("mgmt-domain", spec={})
    assert ret["result"] is True
    assert "already complete" in ret["comment"]


def test_complete_resumes_in_progress(monkeypatch):
    monkeypatch.setattr(
        c, "list_", lambda o, profile=None: [{"id": "sddc-1", "status": "IN_PROGRESS"}]
    )
    monkeypatch.setattr(
        c,
        "wait",
        lambda o, sid, timeout=None, profile=None: {"status": "COMPLETED_WITH_SUCCESS"},
    )
    monkeypatch.setattr(c, "submit", lambda *a, **kw: pytest.fail("should not submit"))
    ret = st.complete("mgmt-domain", spec={})
    assert ret["changes"]["sddc_id"] == "sddc-1"
    assert ret["changes"]["status"] == "COMPLETED_WITH_SUCCESS"


def test_complete_fresh_submission(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "list_", lambda o, profile=None: [])
    monkeypatch.setattr(c, "validate", lambda o, s, profile=None: {"id": "val-1"})
    monkeypatch.setattr(
        c,
        "wait_validation",
        lambda o, vid, timeout=None, profile=None: {"resultStatus": "SUCCEEDED"},
    )
    monkeypatch.setattr(
        c, "submit", lambda o, s, profile=None: calls.append(s) or {"id": "sddc-new"}
    )
    monkeypatch.setattr(
        c, "wait", lambda o, sid, timeout=None, profile=None: {"status": "COMPLETED_WITH_SUCCESS"}
    )
    ret = st.complete("mgmt", spec={"hosts": [1, 2, 3]})
    assert ret["changes"]["sddc_id"] == "sddc-new"
    assert calls == [{"hosts": [1, 2, 3]}]


def test_complete_refuses_prior_failure(monkeypatch):
    monkeypatch.setattr(c, "list_", lambda o, profile=None: [{"id": "sddc-1", "status": "FAILED"}])
    monkeypatch.setattr(c, "submit", lambda *a, **kw: pytest.fail("should not submit"))
    ret = st.complete("mgmt", spec={})
    assert ret["result"] is False
    assert "manual retry" in ret["comment"]


def test_complete_test_mode(monkeypatch, opts):
    opts["test"] = True
    monkeypatch.setattr(c, "list_", lambda o, profile=None: [])
    monkeypatch.setattr(c, "submit", lambda *a, **kw: pytest.fail("should not submit"))
    ret = st.complete("mgmt", spec={})
    assert ret["result"] is None
