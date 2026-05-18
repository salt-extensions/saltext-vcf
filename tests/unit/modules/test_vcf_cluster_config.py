"""Tests for modules.vcf_cluster_config."""

import pytest
import responses

from saltext.vcf.modules import vcf_cluster_config as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_enablement_get(vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/esx/settings/clusters/c1/enablement/configuration",
        json={"enabled": False},
        status=200,
    )
    assert mod.enablement_get("c1") == {"enabled": False}


def test_configuration_get_returns_none_when_not_enabled(vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/esx/settings/clusters/c1/configuration",
        status=400,
    )
    assert mod.configuration_get("c1") is None


def test_drafts_list(vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/esx/settings/clusters/c1/configuration/drafts",
        json=[],
        status=200,
    )
    assert mod.drafts_list("c1") == []


def test_draft_create_returns_id(vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/esx/settings/clusters/c1/configuration/drafts",
        json="draft-99",
        status=200,
    )
    assert mod.draft_create("c1") == "draft-99"


def test_draft_apply(vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/esx/settings/clusters/c1/configuration/drafts/d1",
        json="task-1",
        status=200,
    )
    assert mod.draft_apply("c1", "d1") == "task-1"
    assert "action=apply" in vcenter_authed.calls[-1].request.url
