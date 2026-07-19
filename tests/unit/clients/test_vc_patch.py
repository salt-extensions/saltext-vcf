"""Tests for clients.vc_patch (vCenter VAMI appliance-update REST API)."""

import pytest
import requests
import responses

from saltext.vcf.clients import vc_patch as c


def _body(call):
    body = call.request.body
    return body.decode() if hasattr(body, "decode") else body


def test_get_update_policy(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/policy",
        json={"value": {"auto_stage": False}},
        status=200,
    )
    assert c.get_update_policy(opts) == {"value": {"auto_stage": False}}


def test_set_update_policy_always_sends_full_body(opts, vcenter_authed):
    vcenter_authed.add(
        responses.PUT,
        "https://vc.test/rest/appliance/update/policy",
        status=204,
    )
    c.set_update_policy(opts, "http://repo.example.com/vcsa/")
    call = vcenter_authed.calls[-1]
    body = _body(call)
    assert '"custom_URL": "http://repo.example.com/vcsa/"' in body
    assert '"auto_stage": false' in body
    assert '"check_schedule": []' in body
    assert '"username": ""' in body
    assert '"password": ""' in body


def test_list_pending_updates_forces_source_type_when_url_given(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/pending",
        json={"value": []},
        status=200,
    )
    c.list_pending_updates(opts, repository_url="http://repo.example.com/vcsa/")
    call = vcenter_authed.calls[-1]
    assert "source_type=LOCAL_AND_URL" in call.request.url
    assert "url=http" in call.request.url


def test_get_pending_update_quotes_version(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/pending/9.0.1.0%2B12345",
        json={"value": {"version": "9.0.1.0+12345"}},
        status=200,
    )
    out = c.get_pending_update(opts, "9.0.1.0+12345")
    assert out == {"value": {"version": "9.0.1.0+12345"}}


def test_precheck_no_body_without_component(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/rest/appliance/update/pending/9.0",
        status=200,
    )
    c.precheck(opts, "9.0")
    call = vcenter_authed.calls[-1]
    assert "action=precheck" in call.request.url
    assert call.request.body is None


def test_precheck_with_component(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/rest/appliance/update/pending/9.0",
        status=200,
    )
    c.precheck(opts, "9.0", component="lifecycle-manager")
    call = vcenter_authed.calls[-1]
    assert '"component": "lifecycle-manager"' in _body(call)


def test_stage_no_body_without_component(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/rest/appliance/update/pending/9.0",
        status=200,
    )
    c.stage(opts, "9.0")
    call = vcenter_authed.calls[-1]
    assert "action=stage" in call.request.url
    assert call.request.body is None


def test_install_always_sends_vmdir_password(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/rest/appliance/update/pending/9.0",
        status=200,
    )
    c.install(opts, "9.0", "s3cret")
    call = vcenter_authed.calls[-1]
    assert "action=install" in call.request.url
    body = _body(call)
    assert '"key": "vmdir.password"' in body
    assert '"value": "s3cret"' in body


def test_get_staged_update_404_returns_error_body_not_raise(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/staged",
        json={"error_type": "NOT_FOUND"},
        status=404,
    )
    assert c.get_staged_update(opts) == {"error_type": "NOT_FOUND"}


def test_get_staged_update_404_empty_body_returns_empty_dict(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/staged",
        status=404,
    )
    assert c.get_staged_update(opts) == {}


def test_get_staged_update_500_propagates(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/staged",
        status=500,
    )
    with pytest.raises(requests.HTTPError):
        c.get_staged_update(opts)


def test_delete_staged_update_404_is_tolerated(opts, vcenter_authed):
    vcenter_authed.add(
        responses.DELETE,
        "https://vc.test/rest/appliance/update/staged",
        status=404,
    )
    assert c.delete_staged_update(opts) == {}


# ---------------------------------------------------------------------------
# staged_matches (pure function, no HTTP)
# ---------------------------------------------------------------------------


def test_staged_matches_empty_is_false():
    assert c.staged_matches({}) is False
    assert c.staged_matches(None) is False
    assert c.staged_matches({"value": None}) is False
    assert c.staged_matches({"value": {}}) is False


def test_staged_matches_no_version_requested_just_needs_nonempty():
    assert c.staged_matches({"value": {"version": "9.0.1.0.12345"}}) is True


def test_staged_matches_exact_version():
    assert c.staged_matches({"value": {"version": "9.0.1.0.12345"}}, "9.0.1.0.12345") is True


def test_staged_matches_prefix_either_direction():
    assert c.staged_matches({"value": {"version": "9.0.1.0.12345"}}, "9.0.1.0") is True
    assert c.staged_matches({"value": {"version": "9.0.1.0"}}, "9.0.1.0.12345") is True


def test_staged_matches_mismatch_is_false():
    assert c.staged_matches({"value": {"version": "9.0.1.0.99999"}}, "9.0.1.0.12345") is False


def test_staged_matches_nested_summary_dict():
    staged = {"value": {"summary": {"version": "9.0.1.0.12345"}}}
    assert c.staged_matches(staged, "9.0.1.0.12345") is True


# ---------------------------------------------------------------------------
# resolve_update_version
# ---------------------------------------------------------------------------


def test_resolve_update_version_direct_lookup_succeeds(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/pending/9.0.1.0.12345",
        json={"value": {"version": "9.0.1.0.12345"}},
        status=200,
    )
    resolved, pending_updates, pending_update = c.resolve_update_version(
        opts, version="9.0.1.0.12345"
    )
    assert resolved == "9.0.1.0.12345"
    assert pending_updates is None
    assert pending_update == {"value": {"version": "9.0.1.0.12345"}}


def test_resolve_update_version_falls_back_to_list_and_match(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/pending/9.0.1.0.12345",
        status=404,
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/pending",
        json={"value": [{"version": "9.0.1.0.12345"}, {"version": "9.0.1.0.99999"}]},
        status=200,
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/pending/9.0.1.0.12345",
        json={"value": {"version": "9.0.1.0.12345", "detail": "full"}},
        status=200,
    )
    resolved, pending_updates, pending_update = c.resolve_update_version(
        opts, version="9.0.1.0.12345"
    )
    assert resolved == "9.0.1.0.12345"
    assert pending_update == {"value": {"version": "9.0.1.0.12345", "detail": "full"}}


def test_resolve_update_version_no_version_takes_first_pending(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/pending",
        json={"value": [{"version": "9.0.1.0.12345"}]},
        status=200,
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/pending/9.0.1.0.12345",
        json={"value": {"version": "9.0.1.0.12345"}},
        status=200,
    )
    resolved, _pending_updates, _pending_update = c.resolve_update_version(opts, version=None)
    assert resolved == "9.0.1.0.12345"


def test_resolve_update_version_raises_when_nothing_pending(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/pending",
        json={"value": []},
        status=200,
    )
    with pytest.raises(RuntimeError, match="No pending VCSA updates"):
        c.resolve_update_version(opts, version=None)


def test_resolve_update_version_raises_when_requested_not_found(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/pending/9.9.9.9",
        status=404,
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/pending",
        json={"value": [{"version": "9.0.1.0.12345"}]},
        status=200,
    )
    with pytest.raises(RuntimeError, match="not found"):
        c.resolve_update_version(opts, version="9.9.9.9")


# ---------------------------------------------------------------------------
# transient/timeout error classification
# ---------------------------------------------------------------------------


def test_is_transient_error_checks_status_code():
    resp = requests.Response()
    resp.status_code = 503
    exc = requests.HTTPError(response=resp)
    assert c.is_transient_error(exc) is True


def test_is_transient_error_false_for_non_transient_status():
    resp = requests.Response()
    resp.status_code = 400
    exc = requests.HTTPError(response=resp)
    assert c.is_transient_error(exc) is False


def test_is_stage_timeout_error_matches_response_body():
    resp = requests.Response()
    resp.status_code = 500
    resp._content = b"Timeout happens while waiting for task out file /tmp/x"
    exc = requests.HTTPError(response=resp)
    assert c.is_stage_timeout_error(exc) is True


def test_is_staging_in_progress_error_matches_response_body():
    resp = requests.Response()
    resp.status_code = 400
    resp._content = b"precheck.not_allowed_error: Update staging is in progress"
    exc = requests.HTTPError(response=resp)
    assert c.is_staging_in_progress_error(exc) is True


# ---------------------------------------------------------------------------
# monitor_stage / monitor_install / wait_for_staged_update
# ---------------------------------------------------------------------------


def test_monitor_stage_returns_on_match(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/staged",
        json={"value": {"version": "9.0.1.0.12345"}},
        status=200,
    )
    result = c.monitor_stage(opts, version="9.0.1.0.12345", poll_interval=0, timeout=5)
    assert result["success"] is True
    assert result["state"] == "STAGED"


def test_monitor_stage_raises_on_stage_failed(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/staged",
        status=404,
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update",
        json={"value": {"state": "STAGE_FAILED"}},
        status=200,
    )
    with pytest.raises(RuntimeError, match="VCSA stage failed"):
        c.monitor_stage(opts, version="9.0", poll_interval=0, timeout=5)


def test_monitor_stage_tolerates_transient_then_succeeds(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET, "https://vc.test/rest/appliance/update/staged", status=404
    )
    vcenter_authed.add(
        responses.GET, "https://vc.test/rest/appliance/update", status=503
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/staged",
        json={"value": {"version": "9.0"}},
        status=200,
    )
    result = c.monitor_stage(opts, version="9.0", poll_interval=0, timeout=5)
    assert result["success"] is True


def test_monitor_install_returns_on_up_to_date(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update",
        json={"value": {"state": "UP_TO_DATE"}},
        status=200,
    )
    result = c.monitor_install(opts, poll_interval=0, timeout=5)
    assert result["success"] is True
    assert result["state"] == "UP_TO_DATE"


def test_monitor_install_raises_on_install_failed(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update",
        json={"value": {"state": "INSTALL_FAILED"}},
        status=200,
    )
    with pytest.raises(RuntimeError, match="Install failed"):
        c.monitor_install(opts, poll_interval=0, timeout=5)


def test_wait_for_staged_update_polls_until_match(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET, "https://vc.test/rest/appliance/update/staged", status=404
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/rest/appliance/update/staged",
        json={"value": {"version": "9.0"}},
        status=200,
    )
    result = c.wait_for_staged_update(opts, version="9.0", poll_interval=0, timeout=5)
    assert result["success"] is True


def test_wait_for_staged_update_times_out(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET, "https://vc.test/rest/appliance/update/staged", status=404
    )
    with pytest.raises(TimeoutError):
        c.wait_for_staged_update(opts, version="9.0", poll_interval=0, timeout=0)
