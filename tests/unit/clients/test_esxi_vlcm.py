"""Tests for clients.esxi_vlcm (vCenter ESX Lifecycle Manager / vLCM API)."""

import pytest
import requests
import responses

from saltext.vcf.clients import esxi_vlcm as c


def _body(call):
    body = call.request.body
    return body.decode() if hasattr(body, "decode") else body


def test_online_depot_list(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/esx/settings/depots/online",
        json=[{"url": "https://hostupdate.vmware.com/x.xml"}],
        status=200,
    )
    assert c.online_depot_list(opts) == [{"url": "https://hostupdate.vmware.com/x.xml"}]


def test_offline_depot_create_drops_none_fields(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/esx/settings/depots/offline",
        json="task-1",
        status=200,
    )
    resp = c.offline_depot_create(opts, {"location": "http://repo/depot.zip", "description": None})
    assert resp == "task-1"
    call = vcenter_authed.calls[-1]
    assert "vmw-task=true" in call.request.url
    assert "description" not in _body(call)


def test_depot_sync_success(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/esx/settings/depots",
        json="task-2",
        status=200,
    )
    assert c.depot_sync(opts) == "task-2"
    assert "action=sync" in vcenter_authed.calls[-1].request.url


def test_depot_sync_404_is_skipped(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/esx/settings/depots",
        status=404,
    )
    assert c.depot_sync(opts) == {"skipped": True}


def test_depot_sync_other_error_propagates(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/esx/settings/depots",
        status=500,
    )
    with pytest.raises(requests.HTTPError):
        c.depot_sync(opts)


def test_desired_image_get(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/esx/settings/clusters/c1/software",
        json={"base_image": {"version": "9.2.0.0.1"}},
        status=200,
    )
    assert c.desired_image_get(opts, "c1") == {"base_image": {"version": "9.2.0.0.1"}}


def test_draft_import_software_spec_sends_json_string(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/esx/settings/clusters/c1/software/drafts",
        json="1",
        status=200,
    )
    resp = c.draft_import_software_spec(opts, "c1", {"base_image": {"version": "1.0"}})
    assert resp == "1"
    call = vcenter_authed.calls[-1]
    assert "action=import-software-spec" in call.request.url
    # Not a vmw-task action — it always completes synchronously.
    assert "vmw-task" not in call.request.url
    assert '"source_type": "JSON_STRING"' in _body(call)


def test_draft_commit_with_message(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/esx/settings/clusters/c1/software/drafts/d1",
        json="task-4",
        status=200,
    )
    assert c.draft_commit(opts, "c1", "d1", message="hi") == "task-4"
    call = vcenter_authed.calls[-1]
    assert "action=commit" in call.request.url
    assert '"message": "hi"' in _body(call)


def test_draft_commit_defaults_message_to_empty_string(opts, vcenter_authed):
    """A 400 was hit in production when no body was sent at all for a bare commit."""
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/esx/settings/clusters/c1/software/drafts/d1",
        json="task-4",
        status=200,
    )
    c.draft_commit(opts, "c1", "d1")
    call = vcenter_authed.calls[-1]
    assert '"message": ""' in _body(call)


def test_apply_policy_get_and_set(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/esx/settings/clusters/c1/policies/apply",
        json={"disable_hac": True},
        status=200,
    )
    assert c.apply_policy_get(opts, "c1") == {"disable_hac": True}
    vcenter_authed.add(
        responses.PUT,
        "https://vc.test/api/esx/settings/clusters/c1/policies/apply",
        status=204,
    )
    c.apply_policy_set(opts, "c1", {"disable_hac": True})


def test_remediate_body_has_no_hosts_field(opts, vcenter_authed):
    """``apply``'s body only ever has ``accept_eula`` — unlike scan/stage, no hosts filter."""
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/esx/settings/clusters/c1/software",
        json="task-5",
        status=200,
    )
    resp = c.remediate(opts, "c1")
    assert resp == "task-5"
    call = vcenter_authed.calls[-1]
    assert "action=apply" in call.request.url
    assert "hosts" not in _body(call)
    assert '"accept_eula": true' in _body(call)


def test_compliance_scan_defaults_commit_and_hosts(opts, vcenter_authed):
    """A missing body was rejected with 400 in production for scan/check/stage too."""
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/esx/settings/clusters/c1/software",
        json="task-6",
        status=200,
    )
    c.compliance_scan(opts, "c1")
    call = vcenter_authed.calls[-1]
    assert "action=scan" in call.request.url
    assert '"commit": "1"' in _body(call)
    assert '"hosts": []' in _body(call)


def test_precheck_body_has_only_commit(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/esx/settings/clusters/c1/software",
        json="task-7",
        status=200,
    )
    c.precheck(opts, "c1")
    call = vcenter_authed.calls[-1]
    assert "action=check" in call.request.url
    assert '"commit": "1"' in _body(call)
    assert "hosts" not in _body(call)


def test_stage_defaults_commit_and_hosts(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/esx/settings/clusters/c1/software",
        json="task-8",
        status=200,
    )
    c.stage(opts, "c1")
    call = vcenter_authed.calls[-1]
    assert "action=stage" in call.request.url
    assert '"commit": "1"' in _body(call)
    assert '"hosts": []' in _body(call)


def test_last_check_result_404_to_none(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/esx/settings/clusters/c1/software/reports/last-check-result",
        status=404,
    )
    assert c.last_check_result(opts, "c1") is None


def test_last_check_result_500_propagates(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/esx/settings/clusters/c1/software/reports/last-check-result",
        status=500,
    )
    with pytest.raises(requests.HTTPError):
        c.last_check_result(opts, "c1")


def test_task_id_extraction_bare_string():
    assert c._task_id("task-1") == "task-1"  # pylint: disable=protected-access


def test_task_id_extraction_wrapped_value():
    assert c._task_id({"value": "task-2"}) == "task-2"  # pylint: disable=protected-access


def test_wait_for_task_polls_until_succeeded(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/cis/tasks/task-9",
        json={"status": "RUNNING"},
        status=200,
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/cis/tasks/task-9",
        json={"status": "SUCCEEDED"},
        status=200,
    )
    task = c.wait_for_task(opts, {"value": "task-9"}, timeout=5, poll_interval=0)
    assert task["status"] == "SUCCEEDED"


def test_wait_for_task_raises_on_failure(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/cis/tasks/task-9",
        json={"status": "FAILED"},
        status=200,
    )
    with pytest.raises(RuntimeError):
        c.wait_for_task(opts, "task-9", timeout=5, poll_interval=0)
