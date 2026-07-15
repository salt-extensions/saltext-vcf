"""Tests for clients.nsx_upgrade."""

import json

import pytest
import responses

from saltext.vcf.clients import nsx_upgrade as nu

_BASE = "https://nsx.test/api/v1/upgrade"


# -- status / history ----------------------------------------------------


def test_status_summary(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{_BASE}/status-summary",
        json={"overall_upgrade_status": "IN_PROGRESS", "components": []},
        status=200,
    )
    out = nu.status_summary(opts)
    assert out["overall_upgrade_status"] == "IN_PROGRESS"


def test_history(opts, mocked_responses):
    mocked_responses.add(responses.GET, f"{_BASE}/history", json={"results": []}, status=200)
    assert nu.history(opts) == {"results": []}


# -- plan controls -------------------------------------------------------


def test_start_sends_action_query(opts, mocked_responses):
    mocked_responses.add(responses.POST, f"{_BASE}/plan", json={}, status=200)
    nu.start(opts)
    assert "action=start" in mocked_responses.calls[-1].request.url


def test_pause(opts, mocked_responses):
    mocked_responses.add(responses.POST, f"{_BASE}/plan", json={}, status=200)
    nu.pause(opts)
    assert "action=pause" in mocked_responses.calls[-1].request.url


def test_resume(opts, mocked_responses):
    mocked_responses.add(responses.POST, f"{_BASE}/plan", json={}, status=200)
    nu.resume(opts)
    assert "action=resume" in mocked_responses.calls[-1].request.url


def test_reset(opts, mocked_responses):
    mocked_responses.add(responses.POST, f"{_BASE}/plan", json={}, status=200)
    nu.reset(opts)
    assert "action=reset" in mocked_responses.calls[-1].request.url


def test_plan_settings_round_trip(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{_BASE}/plan/settings",
        json={"parallel": True},
        status=200,
    )
    assert nu.get_plan_settings(opts) == {"parallel": True}

    mocked_responses.add(responses.PUT, f"{_BASE}/plan/settings", json={}, status=200)
    nu.update_plan_settings(opts, {"parallel": False})
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body == {"parallel": False}


# -- upgrade unit groups -----------------------------------------------


def test_list_groups(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        f"{_BASE}/upgrade-unit-groups",
        json={"results": [{"id": "g-1"}]},
        status=200,
    )
    assert nu.list_groups(opts) == {"results": [{"id": "g-1"}]}


def test_get_group_or_none_returns_none_on_404(opts, mocked_responses):
    mocked_responses.add(responses.GET, f"{_BASE}/upgrade-unit-groups/missing", status=404)
    assert nu.get_group_or_none(opts, "missing") is None


def test_create_group_sends_spec(opts, mocked_responses):
    mocked_responses.add(
        responses.POST,
        f"{_BASE}/upgrade-unit-groups",
        json={"id": "g-1"},
        status=200,
    )
    spec = {
        "display_name": "edges",
        "type": "EDGE",
        "upgrade_units": [{"id": "e-1"}],
        "enabled": True,
        "parallel": True,
    }
    nu.create_group(opts, spec)
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body == spec


# -- upgrade units ------------------------------------------------------


def test_list_units_filters_by_group(opts, mocked_responses):
    mocked_responses.add(responses.GET, f"{_BASE}/upgrade-units", json={"results": []}, status=200)
    nu.list_units(opts, group_id="g-1")
    assert "upgrade_unit_group_id=g-1" in mocked_responses.calls[-1].request.url


# -- bundles ------------------------------------------------------------


def test_list_bundles(opts, mocked_responses):
    mocked_responses.add(
        responses.GET, f"{_BASE}/upgrade-bundles", json={"results": []}, status=200
    )
    assert nu.list_bundles(opts) == {"results": []}


# -- waiter -------------------------------------------------------------


def test_wait_for_completion_success(opts, mocked_responses, monkeypatch):
    mocked_responses.add(
        responses.GET,
        f"{_BASE}/status-summary",
        json={"overall_upgrade_status": "IN_PROGRESS"},
        status=200,
    )
    mocked_responses.add(
        responses.GET,
        f"{_BASE}/status-summary",
        json={"overall_upgrade_status": "SUCCESS"},
        status=200,
    )
    monkeypatch.setattr(nu.time, "sleep", lambda s: None)
    out = nu.wait_for_completion(opts, timeout=60, poll_interval=0)
    assert out["overall_upgrade_status"] == "SUCCESS"


def test_wait_for_completion_failure(opts, mocked_responses, monkeypatch):
    mocked_responses.add(
        responses.GET,
        f"{_BASE}/status-summary",
        json={"overall_upgrade_status": "FAILED"},
        status=200,
    )
    monkeypatch.setattr(nu.time, "sleep", lambda s: None)
    with pytest.raises(RuntimeError, match="FAILED"):
        nu.wait_for_completion(opts, timeout=60, poll_interval=0)


def test_wait_for_completion_timeout(opts, mocked_responses, monkeypatch):
    mocked_responses.add(
        responses.GET,
        f"{_BASE}/status-summary",
        json={"overall_upgrade_status": "IN_PROGRESS"},
        status=200,
    )
    times = iter([0.0, 100.0])
    monkeypatch.setattr(nu.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(nu.time, "sleep", lambda s: None)
    with pytest.raises(TimeoutError):
        nu.wait_for_completion(opts, timeout=10, poll_interval=0)
