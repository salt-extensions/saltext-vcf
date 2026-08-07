"""Tests for clients.vcenter_localos_user (VAMI local-accounts REST)."""

import json

import pytest
import requests
import responses

from saltext.vcf.clients import vcenter_localos_user as c


def test_get_or_none_404(opts, mocked_responses, vcenter_authed):
    mocked_responses.add(
        responses.GET,
        "https://vc.test/api/appliance/local-accounts/bob",
        status=404,
    )
    assert c.get_or_none(opts, "bob") is None


def test_get_or_none_found(opts, mocked_responses, vcenter_authed):
    mocked_responses.add(
        responses.GET,
        "https://vc.test/api/appliance/local-accounts/bob",
        json={"username": "bob", "roles": ["operator"], "enabled": True},
        status=200,
    )
    result = c.get_or_none(opts, "bob")
    assert result["username"] == "bob"


def test_get_reraises_non_404(opts, mocked_responses, vcenter_authed):
    mocked_responses.add(
        responses.GET,
        "https://vc.test/api/appliance/local-accounts/bob",
        status=500,
    )
    with pytest.raises(requests.HTTPError):
        c.get_or_none(opts, "bob")


def test_create_posts_expected_body(opts, mocked_responses, vcenter_authed):
    mocked_responses.add(
        responses.POST,
        "https://vc.test/api/appliance/local-accounts/bob",
        json={},
        status=200,
    )
    c.create(opts, "bob", "s3cret", ["operator"], enabled=True, email="bob@example.test")
    req = mocked_responses.calls[-1].request
    assert req.method == "POST"
    body = json.loads(req.body)
    assert body == {
        "password": "s3cret",
        "roles": ["operator"],
        "enabled": True,
        "email": "bob@example.test",
    }


def test_update_patches(opts, mocked_responses, vcenter_authed):
    mocked_responses.add(
        responses.PATCH,
        "https://vc.test/api/appliance/local-accounts/bob",
        json={},
        status=200,
    )
    c.update(opts, "bob", enabled=False)
    req = mocked_responses.calls[-1].request
    assert req.method == "PATCH"


def test_delete(opts, mocked_responses, vcenter_authed):
    mocked_responses.add(
        responses.DELETE,
        "https://vc.test/api/appliance/local-accounts/bob",
        status=204,
    )
    c.delete(opts, "bob")
    req = mocked_responses.calls[-1].request
    assert req.method == "DELETE"
