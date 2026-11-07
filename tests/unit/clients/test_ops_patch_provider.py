"""Tests for clients.ops_patch_provider upgrade monitoring."""

import pytest

from saltext.vcf.clients import ops_patch_provider as mod
from saltext.vcf.clients.ops_patch_provider import OpsPatchProvider

PAK = "vRealizeOperationsManagerEnterprise-912025885555"
PATH = f"/casa/upgrade/cluster/pak/{PAK}/status"


def status(cluster, slice_status="", pak_state="", slices=1):
    """Shape of a CASA pak status response, including the keys that contain the word 'failed'."""
    return {
        "path": PATH,
        "response": {
            "cluster_pak_install_status": cluster,
            "slices": [
                {
                    "slice_address": f"node{i}",
                    "http_code": 200,
                    "document": {
                        "pak_id": PAK,
                        "pak_state": pak_state,
                        "pak_install_status": slice_status,
                        "current_action": None,
                        "failed_details": None,
                        "warning_details": None,
                    },
                }
                for i in range(slices)
            ],
            "cluster_data": {"cluster_action_failed": False, "cluster_action": "NO_ACTION"},
        },
    }


@pytest.fixture
def provider(monkeypatch):
    prov = OpsPatchProvider.__new__(OpsPatchProvider)
    prov.log = mod.logging.getLogger("test")
    prov.sleeps = []
    prov.calls = []
    monkeypatch.setattr(mod.time, "sleep", prov.sleeps.append)
    return prov


def feed(provider, *responses):
    """Make get_pak_status return/raise each response in turn."""
    queue = list(responses)

    def _get(**kwargs):
        provider.calls.append(kwargs)
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    provider.get_pak_status = _get


def test_completed_succeeds(provider):
    feed(provider, status("COMPLETED", "COMPLETED", "INSTALLED"))
    result = provider.wait_for_upgrade_completion(pak_id=PAK)
    assert result["success"] is True
    assert result["progress"]["cluster_status"] == "COMPLETED"


def test_failed_key_names_do_not_count_as_failure(provider):
    """Regression: 'failed_details' / 'cluster_action_failed' keys must not trigger a failure."""
    feed(
        provider,
        status("IN_PROGRESS", "IN_PROGRESS", "INSTALLING"),
        status("COMPLETED", "COMPLETED"),
    )
    result = provider.wait_for_upgrade_completion(pak_id=PAK, poll_interval_seconds=7)
    assert result["success"] is True
    assert provider.sleeps == [7]


def test_initial_candidate_keeps_waiting(provider):
    feed(
        provider,
        status("CANDIDATE", "INITIAL", "NOT_DISTRIBUTED"),
        status("COMPLETED", "COMPLETED"),
    )
    assert provider.wait_for_upgrade_completion(pak_id=PAK)["success"] is True
    assert len(provider.calls) == 2


def test_slice_failed_raises(provider):
    feed(provider, status("IN_PROGRESS", "FAILED", "INSTALLING"))
    with pytest.raises(mod.CommandExecutionError, match="upgrade failed"):
        provider.wait_for_upgrade_completion(pak_id=PAK)


def test_cluster_failed_raises(provider):
    feed(provider, status("FAILED", "", ""))
    with pytest.raises(mod.CommandExecutionError, match="upgrade failed"):
        provider.wait_for_upgrade_completion(pak_id=PAK)


def test_one_failed_slice_among_many_raises(provider):
    resp = status("IN_PROGRESS", "COMPLETED", "INSTALLED", slices=2)
    resp["response"]["slices"][1]["document"]["pak_install_status"] = "FAILED"
    feed(provider, resp)
    with pytest.raises(mod.CommandExecutionError, match="upgrade failed"):
        provider.wait_for_upgrade_completion(pak_id=PAK)


def test_request_errors_are_transient(provider):
    """Connection errors while Operations restarts are retried, not treated as failure."""
    err = RuntimeError("HTTPSConnectionPool: Failed to establish a new connection")
    feed(provider, err, err, status("COMPLETED", "COMPLETED"))
    assert provider.wait_for_upgrade_completion(pak_id=PAK)["success"] is True
    assert len(provider.calls) == 3


def test_max_transient_errors_raises(provider):
    err = RuntimeError("503 Service Unavailable")
    feed(provider, err, err, err)
    with pytest.raises(mod.CommandExecutionError, match="unavailable after 2 attempts"):
        provider.wait_for_upgrade_completion(pak_id=PAK, max_transient_errors=2)


def test_successful_poll_resets_transient_counter(provider):
    err = RuntimeError("503")
    feed(provider, err, status("IN_PROGRESS", "IN_PROGRESS"), err, status("COMPLETED", "COMPLETED"))
    assert (
        provider.wait_for_upgrade_completion(pak_id=PAK, max_transient_errors=2)["success"] is True
    )


def test_timeout(provider, monkeypatch):
    clock = iter([0, 0, 100, 100])
    monkeypatch.setattr(mod.time, "time", lambda: next(clock))
    feed(provider, status("IN_PROGRESS", "IN_PROGRESS"), status("IN_PROGRESS", "IN_PROGRESS"))
    with pytest.raises(mod.CommandExecutionError, match="Timed out"):
        provider.wait_for_upgrade_completion(pak_id=PAK, timeout_seconds=10)


def test_requires_pak_id_or_path(provider):
    feed(provider)
    with pytest.raises(mod.CommandExecutionError, match="without a pak id"):
        provider.wait_for_upgrade_completion()
    assert provider.calls == []


def test_status_path_is_forwarded(provider):
    feed(provider, status("COMPLETED", "COMPLETED"))
    provider.wait_for_upgrade_completion(pak_status_path=PATH)
    assert provider.calls[0] == {"pak_id": None, "pak_status_path": PATH}


def test_pak_install_state_tolerates_missing_documents():
    state = OpsPatchProvider._pak_install_state(
        {
            "response": {
                "cluster_pak_install_status": "in_progress",
                "slices": [{"slice_address": "n1", "http_code": 503}],
            }
        }
    )
    assert state["cluster_status"] == "IN_PROGRESS"
    assert state["slices"] == [{"address": "n1", "state": "", "status": "", "action": None}]
    assert OpsPatchProvider._pak_install_state(None) == {"cluster_status": "", "slices": []}


def test_get_pak_install_status_returns_cluster_status(provider):
    feed(provider, status("candidate", "CANDIDATE"))
    assert provider.get_pak_install_status(PAK) == "CANDIDATE"


def test_get_pak_install_status_none_when_pak_unknown(provider):
    feed(provider, RuntimeError("HTTP 404"))
    assert provider.get_pak_install_status(PAK) is None


def test_wait_for_pak_candidate(provider):
    feed(
        provider,
        RuntimeError("404"),
        status("INITIAL", "INITIAL"),
        status("CANDIDATE", "CANDIDATE"),
    )
    assert provider.wait_for_pak_candidate(PAK, poll_interval_seconds=3) == "CANDIDATE"
    assert provider.sleeps == [3, 3]


def test_wait_for_pak_candidate_fails_on_failed(provider):
    feed(provider, status("FAILED", "FAILED"))
    with pytest.raises(mod.CommandExecutionError, match="failed after upload"):
        provider.wait_for_pak_candidate(PAK)


def test_wait_for_pak_candidate_times_out(provider, monkeypatch):
    clock = iter([0, 0, 100])
    monkeypatch.setattr(mod.time, "time", lambda: next(clock))
    feed(provider, status("INITIAL", "INITIAL"), status("INITIAL", "INITIAL"))
    with pytest.raises(mod.CommandExecutionError, match="to become CANDIDATE"):
        provider.wait_for_pak_candidate(PAK, timeout_seconds=10)


def test_pak_content_missing_detects_not_distributed(provider):
    feed(provider, status("CANDIDATE", "INITIAL", "NOT_DISTRIBUTED"))
    assert provider.pak_content_missing(PAK) is True


def test_pak_content_present_when_deployed(provider):
    feed(provider, status("CANDIDATE", "CANDIDATE", "DEPLOYED_NEW_UPGRADE_CONTENT"))
    assert provider.pak_content_missing(PAK) is False


def test_pak_content_missing_false_when_status_unreadable(provider):
    feed(provider, RuntimeError("404"))
    assert provider.pak_content_missing(PAK) is False


BASE = ("CANDIDATE", (("DEPLOYED_NEW_UPGRADE_CONTENT", "CANDIDATE", None),))


def test_confirm_started_when_pak_state_advances_while_cluster_stays_candidate(provider):
    """Regression: cluster status stays CANDIDATE while pak_state moves on to VALIDATED / CERT_RENEWED."""
    feed(
        provider,
        status("CANDIDATE", "CANDIDATE", "DEPLOYED_NEW_UPGRADE_CONTENT"),
        status("CANDIDATE", "CANDIDATE", "VALIDATED"),
    )
    snapshot = provider.confirm_pak_install_started(PAK, baseline=BASE, poll_interval_seconds=2)
    assert snapshot[1][0][0] == "VALIDATED"
    assert provider.sleeps == [2]


def test_confirm_started_when_cluster_status_leaves_candidate(provider):
    feed(provider, RuntimeError("502"), status("IN_PROGRESS", "IN_PROGRESS", "INSTALLING"))
    assert provider.confirm_pak_install_started(PAK, baseline=BASE)[0] == "IN_PROGRESS"


def test_confirm_started_when_a_slice_reports_an_action(provider):
    resp = status("CANDIDATE", "CANDIDATE", "VALIDATED")
    resp["response"]["slices"][0]["document"]["current_action"] = "INSTALLING"
    feed(provider, resp)
    assert provider.confirm_pak_install_started(PAK, baseline=BASE) is not None


def test_confirm_not_started_when_nothing_changed(provider, monkeypatch):
    clock = iter([0, 0, 500])
    monkeypatch.setattr(mod.time, "time", lambda: next(clock))
    same = status("CANDIDATE", "CANDIDATE", "DEPLOYED_NEW_UPGRADE_CONTENT")
    feed(provider, same, same)
    assert provider.confirm_pak_install_started(PAK, baseline=BASE, timeout_seconds=10) is None


def test_confirm_raises_on_failed(provider):
    feed(provider, status("FAILED", "FAILED"))
    with pytest.raises(mod.CommandExecutionError, match="install failed"):
        provider.confirm_pak_install_started(PAK)


def test_confirm_unreachable_at_timeout_is_unknown_not_failure(provider, monkeypatch):
    """Operations restarts its services during an upgrade, so an unreachable status is not 'not started'."""
    clock = iter([0, 0, 500])
    monkeypatch.setattr(mod.time, "time", lambda: next(clock))
    feed(provider, RuntimeError("503"), RuntimeError("503"))
    assert provider.confirm_pak_install_started(PAK, baseline=BASE, timeout_seconds=10) == (
        "UNKNOWN",
        (),
    )


@pytest.mark.parametrize("pak_state", ["VALIDATED", "CERT_RENEWED"])
def test_install_underway_when_pak_state_is_past_the_pre_install_states(provider, pak_state):
    feed(provider, status("CANDIDATE", "CANDIDATE", pak_state))
    assert provider.pak_install_underway(PAK) is True


@pytest.mark.parametrize("pak_state", ["NOT_DISTRIBUTED", "DEPLOYED_NEW_UPGRADE_CONTENT", ""])
def test_install_not_underway_in_the_pre_install_states(provider, pak_state):
    feed(provider, status("CANDIDATE", "CANDIDATE", pak_state))
    assert provider.pak_install_underway(PAK) is False


def test_install_underway_when_cluster_status_moves_on(provider):
    feed(provider, status("IN_PROGRESS", "IN_PROGRESS", "DEPLOYED_NEW_UPGRADE_CONTENT"))
    assert provider.pak_install_underway(PAK) is True


def test_install_not_underway_when_status_unreadable(provider):
    feed(provider, RuntimeError("503"))
    assert provider.pak_install_underway(PAK) is False
