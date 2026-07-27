"""Tests for clients.vcfa_lifecycle."""

import json

import pytest
import responses

from saltext.vcf.clients import vcfa_lifecycle as lc

_BASE = "https://vcfa.test/lcm/api"


# -- products / versions -------------------------------------------------


def test_list_products_unwraps_content(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/products",
        json={"content": [{"id": "p-1"}]},
        status=200,
    )
    assert lc.list_products(opts) == [{"id": "p-1"}]


def test_list_products_unwraps_items(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/products",
        json={"items": [{"id": "p-1"}, {"id": "p-2"}]},
        status=200,
    )
    assert [p["id"] for p in lc.list_products(opts)] == ["p-1", "p-2"]


def test_get_product_or_none_returns_none_on_404(opts, vcfa_authed):
    vcfa_authed.add(responses.GET, f"{_BASE}/products/missing", status=404)
    assert lc.get_product_or_none(opts, "missing") is None


def test_list_versions(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/products/p-1/versions",
        json={"content": [{"version": "9.0"}, {"version": "9.1"}]},
        status=200,
    )
    out = lc.list_versions(opts, "p-1")
    assert [v["version"] for v in out] == ["9.0", "9.1"]


# -- upgrades ------------------------------------------------------------


def test_start_upgrade_sends_spec(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        f"{_BASE}/upgrades",
        json={"id": "u-1", "state": "RUNNING"},
        status=200,
    )
    out = lc.start_upgrade(opts, {"productId": "p-1", "targetVersion": "9.1"})
    assert out == {"id": "u-1", "state": "RUNNING"}
    body = json.loads(vcfa_authed.calls[-1].request.body)
    assert body == {"productId": "p-1", "targetVersion": "9.1"}


def test_cancel_upgrade(opts, vcfa_authed):
    vcfa_authed.add(responses.POST, f"{_BASE}/upgrades/u-1/actions", json={}, status=200)
    lc.cancel_upgrade(opts, "u-1")
    body = json.loads(vcfa_authed.calls[-1].request.body)
    assert body == {"action": "CANCEL"}


def test_retry_upgrade(opts, vcfa_authed):
    vcfa_authed.add(responses.POST, f"{_BASE}/upgrades/u-1/actions", json={}, status=200)
    lc.retry_upgrade(opts, "u-1")
    body = json.loads(vcfa_authed.calls[-1].request.body)
    assert body == {"action": "RETRY"}


def test_resume_upgrade(opts, vcfa_authed):
    vcfa_authed.add(responses.POST, f"{_BASE}/upgrades/u-1/actions", json={}, status=200)
    lc.resume_upgrade(opts, "u-1")
    body = json.loads(vcfa_authed.calls[-1].request.body)
    assert body == {"action": "RESUME"}


def test_wait_for_upgrade_succeeds(opts, vcfa_authed, monkeypatch):
    vcfa_authed.add(
        responses.GET, f"{_BASE}/upgrades/u-1", json={"id": "u-1", "state": "RUNNING"}, status=200
    )
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/upgrades/u-1",
        json={"id": "u-1", "state": "SUCCEEDED"},
        status=200,
    )
    monkeypatch.setattr(lc.time, "sleep", lambda s: None)
    assert lc.wait_for_upgrade(opts, "u-1", timeout=60, poll_interval=0)["state"] == "SUCCEEDED"


def test_wait_for_upgrade_accepts_completed(opts, vcfa_authed, monkeypatch):
    """Legacy VCFA versions report ``COMPLETED`` instead of ``SUCCEEDED``."""
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/upgrades/u-1",
        json={"id": "u-1", "status": "COMPLETED"},
        status=200,
    )
    monkeypatch.setattr(lc.time, "sleep", lambda s: None)
    assert lc.wait_for_upgrade(opts, "u-1", timeout=60, poll_interval=0)["status"] == "COMPLETED"


def test_wait_for_upgrade_failure(opts, vcfa_authed, monkeypatch):
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/upgrades/u-1",
        json={"id": "u-1", "state": "FAILED"},
        status=200,
    )
    monkeypatch.setattr(lc.time, "sleep", lambda s: None)
    with pytest.raises(RuntimeError, match="FAILED"):
        lc.wait_for_upgrade(opts, "u-1", timeout=60, poll_interval=0)


def test_wait_for_upgrade_timeout(opts, vcfa_authed, monkeypatch):
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/upgrades/u-1",
        json={"id": "u-1", "state": "RUNNING"},
        status=200,
    )
    times = iter([0.0, 100.0])
    monkeypatch.setattr(lc.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(lc.time, "sleep", lambda s: None)
    with pytest.raises(TimeoutError):
        lc.wait_for_upgrade(opts, "u-1", timeout=10, poll_interval=0)


# -- snapshots -----------------------------------------------------------


def test_create_snapshot(opts, vcfa_authed):
    vcfa_authed.add(responses.POST, f"{_BASE}/snapshots", json={"id": "s-1"}, status=200)
    lc.create_snapshot(opts, {"name": "pre-upgrade", "includeData": True})
    body = json.loads(vcfa_authed.calls[-1].request.body)
    assert body == {"name": "pre-upgrade", "includeData": True}


def test_restore_snapshot(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        f"{_BASE}/snapshots/s-1/restore",
        json={"id": "r-1", "state": "RUNNING"},
        status=200,
    )
    assert lc.restore_snapshot(opts, "s-1") == {"id": "r-1", "state": "RUNNING"}


def test_delete_snapshot(opts, vcfa_authed):
    vcfa_authed.add(responses.DELETE, f"{_BASE}/snapshots/s-1", status=204)
    assert lc.delete_snapshot(opts, "s-1") == {}


# -- patches / baseline management ---------------------------------------


def test_list_patches_prefers_patches_endpoint(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/products/p-1/patches",
        json={"content": [{"version": "9.0.1", "status": "INSTALLED"}]},
        status=200,
    )
    out = lc.list_patches(opts, "p-1")
    assert [e["version"] for e in out] == ["9.0.1"]


def test_list_patches_falls_back_to_versions_on_404(opts, vcfa_authed):
    vcfa_authed.add(responses.GET, f"{_BASE}/products/p-1/patches", status=404)
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/products/p-1/versions",
        json={
            "content": [
                {"version": "9.0.0", "kind": "MAJOR"},
                {"version": "9.0.1", "kind": "PATCH", "status": "INSTALLED"},
                {"version": "9.0.2", "kind": "PATCH", "status": "AVAILABLE"},
            ]
        },
        status=200,
    )
    out = lc.list_patches(opts, "p-1")
    assert sorted(e["version"] for e in out) == ["9.0.1", "9.0.2"]


def test_installed_patches_filters_by_status(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/products/p-1/patches",
        json={
            "content": [
                {"version": "9.0.1", "status": "INSTALLED"},
                {"version": "9.0.2", "status": "AVAILABLE"},
                {"version": "9.0.3", "state": "APPLIED"},
            ]
        },
        status=200,
    )
    out = lc.installed_patches(opts, "p-1")
    assert sorted(e["version"] for e in out) == ["9.0.1", "9.0.3"]


def test_available_patches_filters_by_status(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/products/p-1/patches",
        json={
            "content": [
                {"version": "9.0.1", "status": "INSTALLED"},
                {"version": "9.0.2", "status": "AVAILABLE"},
                {"version": "9.0.3", "status": "STAGED"},
            ]
        },
        status=200,
    )
    out = lc.available_patches(opts, "p-1")
    assert sorted(e["version"] for e in out) == ["9.0.2", "9.0.3"]


def test_installed_patch_versions(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/products/p-1/patches",
        json={
            "content": [
                {"version": "9.0.1", "status": "INSTALLED"},
                {"version": "9.0.2", "status": "AVAILABLE"},
            ]
        },
        status=200,
    )
    assert lc.installed_patch_versions(opts, "p-1") == ["9.0.1"]


def test_find_patch_exact(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/products/p-1/patches",
        json={
            "content": [
                {"version": "9.0.1", "status": "INSTALLED"},
                {"version": "9.0.2", "status": "AVAILABLE"},
            ]
        },
        status=200,
    )
    entry = lc.find_patch(opts, "p-1", "9.0.2")
    assert entry["version"] == "9.0.2"


def test_find_patch_prefix(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/products/p-1/patches",
        json={"content": [{"version": "9.0.2.12345", "status": "AVAILABLE"}]},
        status=200,
    )
    entry = lc.find_patch(opts, "p-1", "9.0.2")
    assert entry["version"] == "9.0.2.12345"


def test_find_patch_missing(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        f"{_BASE}/products/p-1/patches",
        json={"content": [{"version": "9.0.1"}]},
        status=200,
    )
    assert lc.find_patch(opts, "p-1", "9.9.9") is None


def test_is_patch_allowed_exact():
    entry = {"version": "9.0.1"}
    assert lc.is_patch_allowed(entry, ["9.0.1"])
    assert not lc.is_patch_allowed(entry, ["9.0.2"])


def test_is_patch_allowed_prefix():
    entry = {"version": "9.0.1.12345"}
    assert lc.is_patch_allowed(entry, ["9.0.1"])
    assert lc.is_patch_allowed({"version": "9.0.1"}, ["9.0.1.12345"])


def test_is_patch_allowed_none_and_empty():
    assert not lc.is_patch_allowed(None, ["9.0.1"])
    assert not lc.is_patch_allowed({"version": "9.0.1"}, [])
    assert not lc.is_patch_allowed({}, ["9.0.1"])


def test_resolve_patch_version_falls_through_fields():
    assert lc.resolve_patch_version({"version": "9.0.1"}) == "9.0.1"
    assert lc.resolve_patch_version({"name": "9.0.1"}) == "9.0.1"
    assert lc.resolve_patch_version({"id": "abc"}) == "abc"
    assert lc.resolve_patch_version({}) is None


def test_stage_patch_posts_stage_action(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        f"{_BASE}/upgrades",
        json={"id": "u-2", "state": "STAGING"},
        status=200,
    )
    lc.stage_patch(opts, "p-1", "9.0.2")
    body = json.loads(vcfa_authed.calls[-1].request.body)
    assert body == {"productId": "p-1", "targetVersion": "9.0.2", "action": "STAGE"}


def test_apply_patch_posts_apply_action(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        f"{_BASE}/upgrades",
        json={"id": "u-3", "state": "RUNNING"},
        status=200,
    )
    out = lc.apply_patch(opts, "p-1", "9.0.2", options={"reboot": True})
    assert out == {"id": "u-3", "state": "RUNNING"}
    body = json.loads(vcfa_authed.calls[-1].request.body)
    assert body == {
        "productId": "p-1",
        "targetVersion": "9.0.2",
        "action": "APPLY_PATCH",
        "options": {"reboot": True},
    }


def test_unwrap_collection_shapes():
    # pylint: disable=protected-access
    assert lc._unwrap_collection({"content": [1, 2]}) == [1, 2]
    assert lc._unwrap_collection({"items": [3]}) == [3]
    assert lc._unwrap_collection({"patches": [4]}) == [4]
    assert lc._unwrap_collection({"results": [5]}) == [5]
    assert lc._unwrap_collection([6]) == [6]
    assert lc._unwrap_collection({"nope": "x"}) == []
