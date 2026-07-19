"""Tests for modules.vcf_vc_patch."""

import pytest
import responses

from saltext.vcf.modules import vcf_vc_patch as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_get_update_policy(vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/policy",
        json={"value": {"auto_stage": False}},
        status=200,
    )
    assert mod.get_update_policy() == {"value": {"auto_stage": False}}


def test_get_repository_policy_is_alias(vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/policy",
        json={"value": {}},
        status=200,
    )
    assert mod.get_repository_policy() == {"value": {}}


def test_update_repository_policy_pulls_pillar_default(vcenter_authed):
    opts_pillar = mod.__opts__["pillar"]["saltext.vcf"]
    opts_pillar["vc_patch"] = {"repository_url": "http://repo.example.com/vcsa/"}
    vcenter_authed.add(
        responses.PUT,
        "https://vc.test/rest/appliance/update/policy",
        status=204,
    )
    mod.update_repository_policy()
    call = vcenter_authed.calls[-1]
    body = call.request.body
    body = body.decode() if hasattr(body, "decode") else body
    assert "http://repo.example.com/vcsa/" in body


def test_get_pending_update(vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/pending/9.0",
        json={"value": {"version": "9.0"}},
        status=200,
    )
    assert mod.get_pending_update("9.0") == {"value": {"version": "9.0"}}


def test_install_requires_explicit_or_pillar_values(vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/rest/appliance/update/pending/9.0",
        status=200,
    )
    mod.install("9.0", "s3cret")
    call = vcenter_authed.calls[-1]
    body = call.request.body
    body = body.decode() if hasattr(body, "decode") else body
    assert '"value": "s3cret"' in body


def test_resolve_update_version_returns_bare_string(vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/pending/9.0",
        json={"value": {"version": "9.0"}},
        status=200,
    )
    assert mod.resolve_update_version(version="9.0") == "9.0"
