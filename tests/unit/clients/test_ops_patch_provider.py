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
    assert state["slices"] == [{"address": "n1", "state": "", "status": ""}]
    assert OpsPatchProvider._pak_install_state(None) == {"cluster_status": "", "slices": []}
