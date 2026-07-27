"""Tests for VCFA session-policy / IdP / vIDM-peer states."""

import pytest

from saltext.vcf.clients import vcfa_identity_provider as idpc
from saltext.vcf.clients import vcfa_session_policy as spc
from saltext.vcf.clients import vcfa_vidm_peer as vpc
from saltext.vcf.states import vcf_vcfa_identity_provider as idp
from saltext.vcf.states import vcf_vcfa_session_policy as sp
from saltext.vcf.states import vcf_vcfa_vidm_peer as vp


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(sp, "__opts__", opts, raising=False)
    monkeypatch.setattr(idp, "__opts__", opts, raising=False)
    monkeypatch.setattr(vp, "__opts__", opts, raising=False)


# -- session_policy ---------------------------------------------------


@pytest.fixture
def sp_stub(monkeypatch):
    state = {"current": None, "set_calls": []}

    def _get(o, org, path=None, profile=None):
        return state["current"]

    def _set(o, org, **kw):
        state["set_calls"].append((org, kw))

    monkeypatch.setattr(spc, "session_policy_get", _get)
    monkeypatch.setattr(spc, "session_policy_set", _set)
    return state


def test_sp_configured_idempotent(sp_stub):
    sp_stub["current"] = {"maxAuthFailures": 15, "inactiveTimeoutSeconds": 1800}
    ret = sp.configured("org-1")
    assert ret["changes"] == {}
    assert ret["result"] is True
    assert not sp_stub["set_calls"]


def test_sp_configured_updates_when_out_of_compliance(sp_stub):
    sp_stub["current"] = {"maxAuthFailures": 5, "inactiveTimeoutSeconds": 900}
    ret = sp.configured("org-1")
    assert "maxAuthFailures" in ret["changes"]
    assert "inactiveTimeoutSeconds" in ret["changes"]
    assert sp_stub["set_calls"]


def test_sp_configured_missing_resource_fails(sp_stub):
    sp_stub["current"] = None
    ret = sp.configured("org-x")
    assert ret["result"] is False


def test_sp_configured_test_mode(sp_stub, monkeypatch):
    sp_stub["current"] = {"maxAuthFailures": 5, "inactiveTimeoutSeconds": 900}
    monkeypatch.setitem(sp.__opts__, "test", True)
    ret = sp.configured("org-1")
    assert ret["result"] is None
    assert not sp_stub["set_calls"]


# -- identity_provider ----------------------------------------------


@pytest.fixture
def idp_stub(monkeypatch):
    state = {"found": None, "created": [], "updated": [], "deleted": []}

    def _find(o, org, name, profile=None):
        return state["found"]

    monkeypatch.setattr(idpc, "find_by_name", _find)
    monkeypatch.setattr(
        idpc,
        "identity_provider_create",
        lambda o, org, spec, profile=None: state["created"].append((org, spec)),
    )
    monkeypatch.setattr(
        idpc,
        "identity_provider_update",
        lambda o, org, idp_id, spec, profile=None: state["updated"].append((idp_id, spec)),
    )
    monkeypatch.setattr(
        idpc,
        "identity_provider_delete",
        lambda o, org, idp_id, profile=None: state["deleted"].append(idp_id),
    )
    return state


def test_idp_present_creates(idp_stub):
    ret = idp.present("corp-ad", "org-1", {"type": "AD", "url": "ldaps://ad"})
    assert ret["changes"] == {"new": "corp-ad"}
    assert idp_stub["created"][0][1]["name"] == "corp-ad"


def test_idp_present_idempotent(idp_stub):
    idp_stub["found"] = {"id": "idp-1", "name": "corp-ad", "type": "AD", "url": "ldaps://ad"}
    ret = idp.present("corp-ad", "org-1", {"type": "AD", "url": "ldaps://ad"})
    assert ret["changes"] == {}


def test_idp_present_updates(idp_stub):
    idp_stub["found"] = {"id": "idp-1", "name": "corp-ad", "type": "AD", "url": "ldaps://old"}
    ret = idp.present("corp-ad", "org-1", {"type": "AD", "url": "ldaps://new"})
    assert "url" in ret["changes"]
    assert idp_stub["updated"][0][0] == "idp-1"


def test_idp_absent_noop(idp_stub):
    ret = idp.absent("corp-ad", "org-1")
    assert ret["changes"] == {}


def test_idp_absent_deletes(idp_stub):
    idp_stub["found"] = {"id": "idp-1", "name": "corp-ad"}
    ret = idp.absent("corp-ad", "org-1")
    assert ret["changes"] == {"deleted": "corp-ad"}
    assert idp_stub["deleted"] == ["idp-1"]


# -- vidm_peer ------------------------------------------------------


@pytest.fixture
def vp_stub(monkeypatch):
    state = {"current": None, "set_calls": []}
    monkeypatch.setattr(vpc, "vidm_peer_get", lambda o, profile=None: state["current"])
    monkeypatch.setattr(
        vpc,
        "vidm_peer_set",
        lambda o, **kw: state["set_calls"].append(kw),
    )
    return state


def test_vp_cert_present_missing_resource(vp_stub):
    vp_stub["current"] = None
    ret = vp.cert_present("prod", "PEM")
    assert ret["result"] is False


def test_vp_cert_present_idempotent(vp_stub):
    vp_stub["current"] = {"peerCertificate": "PEM"}
    ret = vp.cert_present("prod", "PEM")
    assert ret["changes"] == {}


def test_vp_cert_present_replaces(vp_stub):
    vp_stub["current"] = {"peerCertificate": "OLD"}
    ret = vp.cert_present("prod", "NEW")
    assert "peerCertificate" in ret["changes"]
    assert vp_stub["set_calls"] == [{"cert": "NEW", "profile": None}]


def test_vp_cert_present_test_mode(vp_stub, monkeypatch):
    vp_stub["current"] = {"peerCertificate": "OLD"}
    monkeypatch.setitem(vp.__opts__, "test", True)
    ret = vp.cert_present("prod", "NEW")
    assert ret["result"] is None
    assert not vp_stub["set_calls"]
