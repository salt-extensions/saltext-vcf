"""Tests for the NSX Management API exec modules."""

import pytest
import responses

from saltext.vmware.modules import vmware_nsx_cluster
from saltext.vmware.modules import vmware_nsx_compute_collection
from saltext.vmware.modules import vmware_nsx_node
from saltext.vmware.modules import vmware_nsx_role_binding
from saltext.vmware.modules import vmware_nsx_transport_node
from saltext.vmware.modules import vmware_nsx_transport_zone


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    for mod in (
        vmware_nsx_node,
        vmware_nsx_cluster,
        vmware_nsx_transport_zone,
        vmware_nsx_transport_node,
        vmware_nsx_compute_collection,
        vmware_nsx_role_binding,
    ):
        monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_node_get(mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/node",
        json={"node_version": "9.2.0.0"},
        status=200,
    )
    assert vmware_nsx_node.get()["node_version"] == "9.2.0.0"


def test_cluster_status(mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/cluster/status",
        json={"overall_status": "STABLE"},
        status=200,
    )
    assert vmware_nsx_cluster.status()["overall_status"] == "STABLE"


def test_transport_zone_list(mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/transport-zones",
        json={"results": []},
        status=200,
    )
    assert vmware_nsx_transport_zone.list_() == {"results": []}


def test_transport_node_get(mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/transport-nodes/tn1",
        json={"node_id": "tn1"},
        status=200,
    )
    assert vmware_nsx_transport_node.get("tn1") == {"node_id": "tn1"}


def test_compute_collection_list(mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/fabric/compute-collections",
        json={"results": []},
        status=200,
    )
    assert vmware_nsx_compute_collection.list_() == {"results": []}


def test_role_binding_create(mocked_responses):
    mocked_responses.add(
        responses.POST,
        "https://nsx.test/api/v1/aaa/role-bindings",
        json={"id": "rb"},
        status=200,
    )
    vmware_nsx_role_binding.create("alice", "remote_user", [{"role": "auditor"}])
