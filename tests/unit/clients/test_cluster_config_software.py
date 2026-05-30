"""Tests for clients.cluster_config_software (vLCM image apply)."""

import json

import responses

from saltext.vcf.clients import cluster_config_software as cs

_BASE = "https://vc.test/api/esx/settings/clusters/c-1/software"


def test_get_returns_image(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, _BASE, json={"base_image": {"version": "8.0.3"}}, status=200)
    assert cs.get(opts, "c-1") == {"base_image": {"version": "8.0.3"}}


def test_get_returns_none_when_cluster_not_managed(opts, vcenter_authed):
    """vCenter 400 INVALID_ARGUMENT maps to ``None`` (cluster not on single-image)."""
    vcenter_authed.add(responses.GET, _BASE, status=400)
    assert cs.get(opts, "c-1") is None


def test_effective_components(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        f"{_BASE}/effective-components",
        json={"components": []},
        status=200,
    )
    assert cs.effective_components(opts, "c-1") == {"components": []}


def test_solutions(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, f"{_BASE}/solutions", json={"solutions": []}, status=200)
    assert cs.solutions(opts, "c-1") == {"solutions": []}


# -- drafts ---------------------------------------------------------------


def test_draft_create(opts, vcenter_authed):
    vcenter_authed.add(responses.POST, f"{_BASE}/drafts", json="d-1", status=200)
    assert cs.draft_create(opts, "c-1") == "d-1"


def test_draft_update_base_image(opts, vcenter_authed):
    vcenter_authed.add(
        responses.PUT, f"{_BASE}/drafts/d-1/software/base-image", json={}, status=200
    )
    cs.draft_update_base_image(opts, "c-1", "d-1", "8.0.3-23299997")
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {"version": "8.0.3-23299997"}


def test_draft_set_add_on(opts, vcenter_authed):
    vcenter_authed.add(responses.PUT, f"{_BASE}/drafts/d-1/software/add-on", json={}, status=200)
    cs.draft_set_add_on(opts, "c-1", "d-1", "Dell-Addon", "8.0.3.0")
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {"name": "Dell-Addon", "version": "8.0.3.0"}


def test_draft_remove_add_on(opts, vcenter_authed):
    vcenter_authed.add(responses.DELETE, f"{_BASE}/drafts/d-1/software/add-on", status=204)
    assert cs.draft_remove_add_on(opts, "c-1", "d-1") == {}


def test_draft_set_component(opts, vcenter_authed):
    vcenter_authed.add(
        responses.PUT,
        f"{_BASE}/drafts/d-1/software/components/Nvidia-AIOps",
        json={},
        status=200,
    )
    cs.draft_set_component(opts, "c-1", "d-1", "Nvidia-AIOps", "1.2.3")
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {"version": "1.2.3"}


def test_draft_set_hardware_support(opts, vcenter_authed):
    vcenter_authed.add(
        responses.PUT,
        f"{_BASE}/drafts/d-1/software/hardware-support",
        json={},
        status=200,
    )
    cs.draft_set_hardware_support(
        opts, "c-1", "d-1", {"packages": {"Dell": {"pkg": "DELL", "version": "9.0"}}}
    )
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {"packages": {"Dell": {"pkg": "DELL", "version": "9.0"}}}


def test_draft_commit(opts, vcenter_authed):
    vcenter_authed.add(responses.POST, f"{_BASE}/drafts/d-1/commits", json="commit-1", status=200)
    assert cs.draft_commit(opts, "c-1", "d-1") == "commit-1"


# -- actions --------------------------------------------------------------


def test_check_sends_action_query(opts, vcenter_authed):
    vcenter_authed.add(responses.POST, _BASE, json="task-1", status=200)
    assert cs.check(opts, "c-1") == "task-1"
    assert "action=check" in vcenter_authed.calls[-1].request.url


def test_apply_sends_eula_body(opts, vcenter_authed):
    vcenter_authed.add(responses.POST, _BASE, json="task-2", status=200)
    cs.apply(opts, "c-1")
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {"commit_spec": {"accept_eula": True}}
    assert "action=apply" in vcenter_authed.calls[-1].request.url


def test_stage_with_hosts(opts, vcenter_authed):
    vcenter_authed.add(responses.POST, _BASE, json="task-3", status=200)
    cs.stage(opts, "c-1", hosts=["host-1", "host-2"])
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {"hosts": ["host-1", "host-2"]}
    assert "action=stage" in vcenter_authed.calls[-1].request.url


def test_scan(opts, vcenter_authed):
    vcenter_authed.add(responses.POST, _BASE, json="task-4", status=200)
    assert cs.scan(opts, "c-1") == "task-4"
    assert "action=scan" in vcenter_authed.calls[-1].request.url


# -- reports --------------------------------------------------------------


def test_last_apply_result(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        f"{_BASE}/reports/last-apply-result",
        json={"status": "OK"},
        status=200,
    )
    assert cs.last_apply_result(opts, "c-1") == {"status": "OK"}


def test_last_apply_result_returns_none_when_unmanaged(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, f"{_BASE}/reports/last-apply-result", status=400)
    assert cs.last_apply_result(opts, "c-1") is None


def test_last_check_result(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET, f"{_BASE}/reports/last-check-result", json={"status": "OK"}, status=200
    )
    assert cs.last_check_result(opts, "c-1") == {"status": "OK"}


def test_last_compliance_result(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        f"{_BASE}/reports/last-compliance-result",
        json={"status": "OK"},
        status=200,
    )
    assert cs.last_compliance_result(opts, "c-1") == {"status": "OK"}


def test_last_stage_result(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET, f"{_BASE}/reports/last-stage-result", json={"status": "OK"}, status=200
    )
    assert cs.last_stage_result(opts, "c-1") == {"status": "OK"}
