"""Tests for clients.cluster_config (vSphere 9 Configuration Profile API)."""

import pytest
import responses

from saltext.vcf.clients import cluster_config as c


def test_enablement_get(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/esx/settings/clusters/c1/enablement/configuration",
        json={"enabled": True},
        status=200,
    )
    assert c.enablement_get(opts, "c1") == {"enabled": True}


def test_schema_get(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/esx/settings/clusters/c1/configuration/schema",
        json={"schema": {"type": "object"}, "source": "IMAGE_PROFILE"},
        status=200,
    )
    out = c.schema_get(opts, "c1")
    assert out["source"] == "IMAGE_PROFILE"


def test_configuration_get_returns_none_for_400(opts, vcenter_authed):
    """400 INVALID_ARGUMENT for clusters not vLCM-managed → ``None``."""
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/esx/settings/clusters/c1/configuration",
        json={"error_type": "INVALID_ARGUMENT"},
        status=400,
    )
    assert c.configuration_get(opts, "c1") is None


def test_configuration_get_returns_doc_for_200(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/esx/settings/clusters/c1/configuration",
        json={"profile": {"esx": {}}},
        status=200,
    )
    assert c.configuration_get(opts, "c1") == {"profile": {"esx": {}}}


def test_configuration_get_propagates_other_errors(opts, vcenter_authed):
    import requests as r

    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/esx/settings/clusters/c1/configuration",
        status=500,
    )
    with pytest.raises(r.HTTPError):
        c.configuration_get(opts, "c1")


def test_draft_lifecycle(opts, vcenter_authed):
    """Create → get configuration → patch configuration → apply → delete."""
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/esx/settings/clusters/c1/configuration/drafts",
        json="draft-1",
        status=200,
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/esx/settings/clusters/c1/configuration/drafts/draft-1/configuration",
        json={"profile": {}},
        status=200,
    )
    vcenter_authed.add(
        responses.PATCH,
        "https://vc.test/api/esx/settings/clusters/c1/configuration/drafts/draft-1/configuration",
        status=204,
    )
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/esx/settings/clusters/c1/configuration/drafts/draft-1",
        json="task-1",
        status=200,
    )
    vcenter_authed.add(
        responses.DELETE,
        "https://vc.test/api/esx/settings/clusters/c1/configuration/drafts/draft-1",
        status=204,
    )

    assert c.draft_create(opts, "c1") == "draft-1"
    assert c.draft_get_configuration(opts, "c1", "draft-1") == {"profile": {}}
    c.draft_update_configuration(opts, "c1", "draft-1", {"profile": {"k": 1}})
    assert c.draft_apply(opts, "c1", "draft-1") == "task-1"
    c.draft_delete(opts, "c1", "draft-1")
    # confirm apply used ?action=apply
    apply_call = [
        c_
        for c_ in vcenter_authed.calls
        if "drafts/draft-1" in c_.request.url and c_.request.method == "POST"
    ]
    assert any("action=apply" in c_.request.url for c_ in apply_call)


def test_last_apply_result_400_to_none(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/esx/settings/clusters/c1/configuration/reports/last-apply-result",
        status=400,
    )
    assert c.last_apply_result(opts, "c1") is None


def test_profile_helpers_roundtrip():
    doc = {}
    c.set_profile_value(doc, "profile.esx.health.ntp_health.servers", ["a", "b"])
    assert c.get_profile_value(doc, "profile.esx.health.ntp_health.servers") == [
        "a",
        "b",
    ]
    assert doc == {"profile": {"esx": {"health": {"ntp_health": {"servers": ["a", "b"]}}}}}


def test_profile_helpers_missing_path_returns_none():
    assert c.get_profile_value({"profile": {}}, "profile.esx.health.ntp") is None
