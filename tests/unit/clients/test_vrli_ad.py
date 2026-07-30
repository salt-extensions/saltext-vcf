"""Tests for clients.vrli_ad."""

import json

import pytest
import responses

from saltext.vcf.clients import vrli_ad

_URL = "https://vrli.test:9543/api/v2/ad"


def test_get_returns_current_ad_config(opts, vrli_authed):
    vrli_authed.add(responses.GET, _URL, json={"enableAD": False}, status=200)
    assert vrli_ad.get(opts) == {"enableAD": False}


def test_set_posts_spec_verbatim(opts, vrli_authed):
    vrli_authed.add(responses.POST, _URL, json={}, status=200)
    spec = {
        "enableAD": True,
        "domain": "corp.example.com",
        "username": "svc-vrli",
        "password": "secret",
        "connType": "STANDARD",
    }
    vrli_ad.set_(opts, spec)
    body = json.loads(vrli_authed.calls[-1].request.body)
    assert body == spec


def test_set_rejects_invalid_conntype_when_enabling(opts, vrli_authed):
    with pytest.raises(ValueError):
        vrli_ad.set_(
            opts,
            {
                "enableAD": True,
                "domain": "d",
                "username": "u",
                "password": "p",
                "connType": "NOPE",
            },
        )


def test_set_accepts_missing_conntype_when_disabling(opts, vrli_authed):
    vrli_authed.add(responses.POST, _URL, json={}, status=200)
    # No connType supplied but enableAD=False → should not validate connType.
    vrli_ad.set_(opts, {"enableAD": False})


def test_disable_shortcut_posts_enable_ad_false(opts, vrli_authed):
    vrli_authed.add(responses.POST, _URL, json={}, status=200)
    vrli_ad.disable(opts)
    body = json.loads(vrli_authed.calls[-1].request.body)
    assert body == {"enableAD": False}
