"""Tests for the VCFA session-policy / IdP / vIDM-peer clients."""

import json

import pytest
import responses

from saltext.vcf.clients import vcfa_identity_provider as idp
from saltext.vcf.clients import vcfa_session_policy as sp
from saltext.vcf.clients import vcfa_vidm_peer as vp


# -- session_policy ---------------------------------------------------


def test_session_policy_get(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/csp/gateway/am/api/orgs/org-1/session-policy",
        json={"maxAuthFailures": 5, "inactiveTimeoutSeconds": 900},
        status=200,
    )
    out = sp.session_policy_get(opts, "org-1")
    assert out == {"maxAuthFailures": 5, "inactiveTimeoutSeconds": 900}


def test_session_policy_get_none_on_404(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/csp/gateway/am/api/orgs/org-x/session-policy",
        json={"error": "not found"},
        status=404,
    )
    assert sp.session_policy_get(opts, "org-x") is None


def test_session_policy_set_merges(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/csp/gateway/am/api/orgs/org-1/session-policy",
        json={"maxAuthFailures": 5, "inactiveTimeoutSeconds": 900, "extra": "x"},
        status=200,
    )
    vcfa_authed.add(
        responses.PUT,
        "https://vcfa.test/csp/gateway/am/api/orgs/org-1/session-policy",
        json={},
        status=200,
    )
    sp.session_policy_set(opts, "org-1", max_auth_failures=15, inactive_timeout=1800)
    body = json.loads(vcfa_authed.calls[-1].request.body)
    assert body["maxAuthFailures"] == 15
    assert body["inactiveTimeoutSeconds"] == 1800
    assert body["extra"] == "x"


def test_session_policy_set_requires_field(opts):
    with pytest.raises(ValueError):
        sp.session_policy_set(opts, "org-1")


def test_session_policy_custom_path(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/csp/gateway/portal/api/orgs/org-1/session-timeout",
        json={"inactiveTimeoutSeconds": 900},
        status=200,
    )
    out = sp.session_policy_get(
        opts,
        "org-1",
        path="/csp/gateway/portal/api/orgs/org-1/session-timeout",
    )
    assert out == {"inactiveTimeoutSeconds": 900}


# -- identity_provider ----------------------------------------------


def test_idp_list(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/csp/gateway/am/api/orgs/org-1/identity-providers",
        json={"items": [{"id": "idp-1", "name": "corp-ad"}]},
        status=200,
    )
    out = idp.identity_provider_list(opts, "org-1")
    assert out == [{"id": "idp-1", "name": "corp-ad"}]


def test_idp_get_or_none_404(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/csp/gateway/am/api/orgs/org-1/identity-providers/missing",
        json={},
        status=404,
    )
    assert idp.identity_provider_get_or_none(opts, "org-1", "missing") is None


def test_idp_find_by_name(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/csp/gateway/am/api/orgs/org-1/identity-providers",
        json={"items": [{"id": "idp-1", "name": "corp-ad"}, {"id": "idp-2", "name": "ldap"}]},
        status=200,
    )
    found = idp.find_by_name(opts, "org-1", "ldap")
    assert found == {"id": "idp-2", "name": "ldap"}


def test_idp_create_update_delete(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        "https://vcfa.test/csp/gateway/am/api/orgs/org-1/identity-providers",
        json={"id": "idp-new"},
        status=200,
    )
    idp.identity_provider_create(opts, "org-1", {"name": "corp-ad", "type": "AD"})
    body = json.loads(vcfa_authed.calls[-1].request.body)
    assert body == {"name": "corp-ad", "type": "AD"}

    vcfa_authed.add(
        responses.PUT,
        "https://vcfa.test/csp/gateway/am/api/orgs/org-1/identity-providers/idp-new",
        json={},
        status=200,
    )
    idp.identity_provider_update(opts, "org-1", "idp-new", {"name": "corp-ad", "type": "AD"})

    vcfa_authed.add(
        responses.DELETE,
        "https://vcfa.test/csp/gateway/am/api/orgs/org-1/identity-providers/idp-new",
        status=204,
    )
    assert idp.identity_provider_delete(opts, "org-1", "idp-new") == {}


# -- vidm_peer ------------------------------------------------------


def test_vidm_peer_get(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/provisioning/mgmt/identity-vidm-peer",
        json={"hostAddress": "vidm.example.com", "peerCertificate": "PEMDATA"},
        status=200,
    )
    out = vp.vidm_peer_get(opts)
    assert out["hostAddress"] == "vidm.example.com"


def test_vidm_peer_get_none_on_404(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/provisioning/mgmt/identity-vidm-peer",
        status=404,
    )
    assert vp.vidm_peer_get(opts) is None


def test_vidm_peer_set_merges(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/provisioning/mgmt/identity-vidm-peer",
        json={"hostAddress": "vidm.example.com", "peerCertificate": "OLD"},
        status=200,
    )
    vcfa_authed.add(
        responses.PUT,
        "https://vcfa.test/provisioning/mgmt/identity-vidm-peer",
        json={},
        status=200,
    )
    vp.vidm_peer_set(opts, cert="NEW-PEM")
    body = json.loads(vcfa_authed.calls[-1].request.body)
    assert body["peerCertificate"] == "NEW-PEM"
    assert body["hostAddress"] == "vidm.example.com"


def test_vidm_peer_set_requires_field(opts):
    with pytest.raises(ValueError):
        vp.vidm_peer_set(opts)


def test_vidm_peer_validate(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        "https://vcfa.test/provisioning/mgmt/identity-vidm-peer/validate",
        json={"valid": True},
        status=200,
    )
    out = vp.vidm_peer_validate(opts, {"hostAddress": "x"})
    assert out == {"valid": True}
