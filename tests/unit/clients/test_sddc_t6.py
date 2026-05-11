"""Tests for the T6 SDDC workload domain lifecycle client surface."""

import time

import pytest
import responses

from saltext.vmware.clients import sddc_avn
from saltext.vmware.clients import sddc_cluster_ops
from saltext.vmware.clients import sddc_domain
from saltext.vmware.clients import sddc_edge_clusters
from saltext.vmware.clients import sddc_license_keys
from saltext.vmware.clients import sddc_system
from saltext.vmware.clients import sddc_tasks
from saltext.vmware.clients import sddc_users

SM = "https://sm.test"


# ---------- domain lifecycle ----------


def test_domain_validate(opts, sddc_authed):
    sddc_authed.add(
        responses.POST,
        f"{SM}/v1/domains/validations",
        json={"executionStatus": "COMPLETED", "resultStatus": "SUCCEEDED"},
        status=200,
    )
    result = sddc_domain.validate(opts, {"name": "wld-01"})
    assert result["executionStatus"] == "COMPLETED"


def test_domain_create_returns_task(opts, sddc_authed):
    sddc_authed.add(
        responses.POST,
        f"{SM}/v1/domains",
        json={"id": "task-1", "status": "IN_PROGRESS"},
        status=202,
    )
    result = sddc_domain.create(opts, {"name": "wld-01"})
    assert result["id"] == "task-1"


def test_domain_update_expands(opts, sddc_authed):
    sddc_authed.add(
        responses.PATCH,
        f"{SM}/v1/domains/d-1",
        json={"id": "task-2", "status": "IN_PROGRESS"},
        status=202,
    )
    result = sddc_domain.update(opts, "d-1", {"clusterSpecs": []})
    assert result["id"] == "task-2"


def test_domain_delete(opts, sddc_authed):
    sddc_authed.add(responses.DELETE, f"{SM}/v1/domains/d-1", status=202)
    result = sddc_domain.delete(opts, "d-1")
    assert result == {}


def test_domain_mark_for_deletion(opts, sddc_authed):
    sddc_authed.add(
        responses.PATCH,
        f"{SM}/v1/domains/d-1",
        json={"markedForDeletion": True},
        status=200,
    )
    result = sddc_domain.mark_for_deletion(opts, "d-1")
    assert result["markedForDeletion"] is True


def test_domain_get_by_name(opts, sddc_authed):
    sddc_authed.add(
        responses.GET,
        f"{SM}/v1/domains",
        json={"elements": [{"id": "d-1", "name": "mgmt"}, {"id": "d-2", "name": "wld-01"}]},
        status=200,
    )
    found = sddc_domain.get_by_name(opts, "wld-01")
    assert found["id"] == "d-2"
    sddc_authed.add(
        responses.GET,
        f"{SM}/v1/domains",
        json={"elements": [{"id": "d-1", "name": "mgmt"}]},
        status=200,
    )
    assert sddc_domain.get_by_name(opts, "missing") is None


def test_domain_list_endpoints(opts, sddc_authed):
    sddc_authed.add(
        responses.GET,
        f"{SM}/v1/domains/d-1/endpoints",
        json={"elements": [{"type": "VCENTER", "url": "https://vc"}]},
        status=200,
    )
    endpoints = sddc_domain.list_endpoints(opts, "d-1")
    assert endpoints["elements"][0]["type"] == "VCENTER"


# ---------- cluster ops ----------


def test_cluster_expand_wraps_spec(opts, sddc_authed):
    sddc_authed.add(
        responses.PATCH,
        f"{SM}/v1/clusters/c-1",
        json={"id": "task-3"},
        status=202,
    )
    result = sddc_cluster_ops.expand(opts, "c-1", [{"id": "h-1"}, {"id": "h-2"}])
    assert result["id"] == "task-3"
    body = sddc_authed.calls[-1].request.body
    assert b"clusterExpansionSpec" in body
    assert b'"id": "h-1"' in body


def test_cluster_shrink_wraps_spec(opts, sddc_authed):
    sddc_authed.add(
        responses.PATCH,
        f"{SM}/v1/clusters/c-1",
        json={"id": "task-4"},
        status=202,
    )
    sddc_cluster_ops.shrink(opts, "c-1", ["h-1"], force=True)
    body = sddc_authed.calls[-1].request.body
    assert b"clusterCompactionSpec" in body
    assert b'"force": true' in body


def test_cluster_validate(opts, sddc_authed):
    sddc_authed.add(
        responses.POST,
        f"{SM}/v1/clusters/validations",
        json={"resultStatus": "SUCCEEDED"},
        status=200,
    )
    result = sddc_cluster_ops.validate(opts, {"clusterSpec": {}})
    assert result["resultStatus"] == "SUCCEEDED"


def test_cluster_mark_for_deletion(opts, sddc_authed):
    sddc_authed.add(responses.PATCH, f"{SM}/v1/clusters/c-1", json={}, status=200)
    sddc_cluster_ops.mark_for_deletion(opts, "c-1")
    body = sddc_authed.calls[-1].request.body
    assert b"markForDeletion" in body


# ---------- edge clusters ----------


def test_edge_cluster_list(opts, sddc_authed):
    sddc_authed.add(responses.GET, f"{SM}/v1/edge-clusters", json={"elements": []}, status=200)
    assert sddc_edge_clusters.list_(opts) == {"elements": []}


def test_edge_cluster_get_or_none_missing(opts, sddc_authed):
    sddc_authed.add(responses.GET, f"{SM}/v1/edge-clusters/missing", status=404)
    assert sddc_edge_clusters.get_or_none(opts, "missing") is None


def test_edge_cluster_validate_and_create(opts, sddc_authed):
    sddc_authed.add(
        responses.POST,
        f"{SM}/v1/edge-cluster-validations",
        json={"resultStatus": "SUCCEEDED"},
        status=200,
    )
    sddc_edge_clusters.validate(opts, {})
    sddc_authed.add(responses.POST, f"{SM}/v1/edge-clusters", json={"id": "task-5"}, status=202)
    result = sddc_edge_clusters.create(opts, {})
    assert result["id"] == "task-5"


def test_edge_cluster_expand_delete(opts, sddc_authed):
    sddc_authed.add(
        responses.PATCH,
        f"{SM}/v1/edge-clusters/e-1",
        json={"id": "task-6"},
        status=202,
    )
    sddc_edge_clusters.expand(opts, "e-1", {"edgeNodeSpecs": []})
    sddc_authed.add(responses.DELETE, f"{SM}/v1/edge-clusters/e-1", status=202)
    sddc_edge_clusters.delete(opts, "e-1")


# ---------- license keys ----------


def test_license_keys_full_lifecycle(opts, sddc_authed):
    sddc_authed.add(responses.GET, f"{SM}/v1/license-keys", json={"elements": []}, status=200)
    sddc_authed.add(responses.POST, f"{SM}/v1/license-keys", json={}, status=200)
    sddc_authed.add(responses.GET, f"{SM}/v1/license-keys/X-X-X", json={"key": "X-X-X"}, status=200)
    sddc_authed.add(responses.GET, f"{SM}/v1/license-keys/missing", status=404)
    sddc_authed.add(responses.DELETE, f"{SM}/v1/license-keys/X-X-X", status=200)
    sddc_authed.add(
        responses.GET, f"{SM}/v1/licensing-info", json=[{"product": "VCENTER"}], status=200
    )

    assert sddc_license_keys.list_(opts) == {"elements": []}
    sddc_license_keys.add(opts, "X-X-X", "VCENTER", description="prod vc")
    body = sddc_authed.calls[-1].request.body
    assert b'"productType": "VCENTER"' in body
    assert sddc_license_keys.get(opts, "X-X-X")["key"] == "X-X-X"
    assert sddc_license_keys.get_or_none(opts, "missing") is None
    sddc_license_keys.delete(opts, "X-X-X")
    assert sddc_license_keys.licensing_info(opts) == [{"product": "VCENTER"}]


# ---------- tasks ----------


def test_task_get(opts, sddc_authed):
    sddc_authed.add(
        responses.GET,
        f"{SM}/v1/tasks/task-1",
        json={"id": "task-1", "status": "Successful"},
        status=200,
    )
    assert sddc_tasks.get(opts, "task-1")["status"] == "Successful"


def test_task_get_or_none_missing(opts, sddc_authed):
    sddc_authed.add(responses.GET, f"{SM}/v1/tasks/missing", status=404)
    assert sddc_tasks.get_or_none(opts, "missing") is None


def test_task_wait_returns_on_success(opts, sddc_authed, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda _: None)
    sddc_authed.add(
        responses.GET,
        f"{SM}/v1/tasks/task-1",
        json={"id": "task-1", "status": "IN_PROGRESS"},
        status=200,
    )
    sddc_authed.add(
        responses.GET,
        f"{SM}/v1/tasks/task-1",
        json={"id": "task-1", "status": "Successful"},
        status=200,
    )
    result = sddc_tasks.wait(opts, "task-1", timeout=5, poll_interval=0)
    assert result["status"] == "Successful"


def test_task_wait_raises_on_failure(opts, sddc_authed, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda _: None)
    sddc_authed.add(
        responses.GET,
        f"{SM}/v1/tasks/task-2",
        json={
            "id": "task-2",
            "status": "Failed",
            "errors": [{"message": "validation failed"}],
        },
        status=200,
    )
    with pytest.raises(RuntimeError, match="validation failed"):
        sddc_tasks.wait(opts, "task-2", timeout=5, poll_interval=0)


def test_task_wait_timeout(opts, sddc_authed, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda _: None)
    sddc_authed.add(
        responses.GET,
        f"{SM}/v1/tasks/task-3",
        json={"id": "task-3", "status": "IN_PROGRESS"},
        status=200,
    )
    # Use a monotonic counter that quickly exceeds the deadline
    fake_time = iter([0.0, 0.0, 1000.0])
    monkeypatch.setattr(time, "monotonic", lambda: next(fake_time))
    with pytest.raises(TimeoutError):
        sddc_tasks.wait(opts, "task-3", timeout=1, poll_interval=0)


def test_task_retry(opts, sddc_authed):
    sddc_authed.add(
        responses.PATCH,
        f"{SM}/v1/tasks/task-x",
        json={"id": "task-x", "status": "IN_PROGRESS"},
        status=200,
    )
    assert sddc_tasks.retry(opts, "task-x")["status"] == "IN_PROGRESS"


# ---------- avn / users / system ----------


def test_avn_list_and_validate(opts, sddc_authed):
    sddc_authed.add(responses.GET, f"{SM}/v1/avns", json=[], status=200)
    sddc_authed.add(
        responses.POST,
        f"{SM}/v1/avn-validations",
        json={"resultStatus": "SUCCEEDED"},
        status=200,
    )
    sddc_avn.list_(opts)
    sddc_avn.validate(opts, {})


def test_user_list_and_add(opts, sddc_authed):
    sddc_authed.add(responses.GET, f"{SM}/v1/users", json={"elements": []}, status=200)
    sddc_authed.add(responses.POST, f"{SM}/v1/users", json={}, status=200)
    sddc_authed.add(responses.GET, f"{SM}/v1/roles", json={"elements": []}, status=200)
    sddc_authed.add(responses.GET, f"{SM}/v1/users/u-1", json={"id": "u-1"}, status=200)
    sddc_authed.add(responses.GET, f"{SM}/v1/users/missing", status=404)
    sddc_authed.add(responses.DELETE, f"{SM}/v1/users/u-1", status=200)

    sddc_users.list_users(opts)
    sddc_users.add_users(opts, [{"name": "ops", "role": "ADMIN"}])
    sddc_users.list_roles(opts)
    sddc_users.get_user(opts, "u-1")
    assert sddc_users.get_user_or_none(opts, "missing") is None
    sddc_users.delete_user(opts, "u-1")


def test_system_info(opts, sddc_authed):
    sddc_authed.add(responses.GET, f"{SM}/v1/system", json={"vcfInstanceName": "lab"}, status=200)
    assert sddc_system.get_system(opts)["vcfInstanceName"] == "lab"


def test_personality_lookups(opts, sddc_authed):
    sddc_authed.add(responses.GET, f"{SM}/v1/personalities", json={"elements": []}, status=200)
    sddc_authed.add(responses.GET, f"{SM}/v1/personalities/p-1", json={"id": "p-1"}, status=200)
    sddc_authed.add(responses.GET, f"{SM}/v1/personalities/missing", status=404)
    sddc_system.list_personalities(opts)
    sddc_system.get_personality(opts, "p-1")
    assert sddc_system.get_personality_or_none(opts, "missing") is None
