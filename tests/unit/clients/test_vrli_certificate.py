"""Tests for clients.vrli_certificate."""

import responses

from saltext.vcf.clients import vrli_certificate as cc

_URL = "https://vrli.test:9543/api/v2/certificate"


def _cert(serial="6a2d06e"):
    return {
        "owner": {"commonName": "VMware Cloud Foundation Operations for Logs"},
        "issuer": {"commonName": "VMware Cloud Foundation Operations for Logs"},
        "serialNum": serial,
        "validityPeriod": {"from": "2026-07-28T01:02:49Z", "until": "2029-07-27T01:02:49Z"},
    }


def test_list_returns_array_shape(opts, vrli_authed):
    vrli_authed.add(responses.GET, _URL, json=[_cert("aa"), _cert("bb")], status=200)
    out = cc.list_(opts)
    assert [c["serialNum"] for c in out] == ["aa", "bb"]


def test_list_handles_dict_shape(opts, vrli_authed):
    """Some older builds return {'certificates': [...]} instead of a bare list."""
    vrli_authed.add(responses.GET, _URL, json={"certificates": [_cert("aa")]}, status=200)
    assert cc.list_(opts)[0]["serialNum"] == "aa"


def test_list_handles_empty(opts, vrli_authed):
    vrli_authed.add(responses.GET, _URL, json=[], status=200)
    assert cc.list_(opts) == []


def test_get_returns_first_or_none(opts, vrli_authed):
    vrli_authed.add(responses.GET, _URL, json=[_cert("aa"), _cert("bb")], status=200)
    assert cc.get(opts)["serialNum"] == "aa"


def test_get_returns_none_on_empty(opts, vrli_authed):
    vrli_authed.add(responses.GET, _URL, json=[], status=200)
    assert cc.get(opts) is None


def test_install_concatenates_pems_in_certificate_field(opts, vrli_authed):
    vrli_authed.add(responses.POST, _URL, json={}, status=200)
    cc.install(opts, "-----BEGIN CERT-----\nAAA\n-----END CERT-----", "KEY", chain_pem=None)
    call = [c for c in vrli_authed.calls if c.request.method == "POST" and _URL in c.request.url][
        -1
    ]
    import json

    body = json.loads(call.request.body)
    assert "certificate" in body
    assert "BEGIN CERT" in body["certificate"]
    assert body["certificate"].strip().endswith("KEY")


def test_install_includes_chain_when_provided(opts, vrli_authed):
    vrli_authed.add(responses.POST, _URL, json={}, status=200)
    cc.install(opts, "LEAF", "KEY", chain_pem="CHAIN")
    import json

    body = json.loads(vrli_authed.calls[-1].request.body)
    # order: leaf, chain, key
    idx_leaf = body["certificate"].find("LEAF")
    idx_chain = body["certificate"].find("CHAIN")
    idx_key = body["certificate"].find("KEY")
    assert 0 <= idx_leaf < idx_chain < idx_key


def test_serial_number_helper(opts, vrli_authed):
    vrli_authed.add(responses.GET, _URL, json=[_cert("deadbeef")], status=200)
    assert cc.serial_number(opts) == "deadbeef"


def test_serial_number_none_when_empty(opts, vrli_authed):
    vrli_authed.add(responses.GET, _URL, json=[], status=200)
    assert cc.serial_number(opts) is None
