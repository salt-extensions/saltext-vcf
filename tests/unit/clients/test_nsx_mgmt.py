"""Tests for the NSX Management API clients."""

import responses

from saltext.vmware.clients import nsx_cluster
from saltext.vmware.clients import nsx_compute_collection
from saltext.vmware.clients import nsx_node
from saltext.vmware.clients import nsx_role_binding
from saltext.vmware.clients import nsx_transport_node
from saltext.vmware.clients import nsx_transport_zone


def test_node_get(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/node",
        json={"node_version": "9.2.0.0"},
        status=200,
    )
    assert nsx_node.get(opts)["node_version"] == "9.2.0.0"


def test_cluster_status(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/cluster/status",
        json={"overall_status": "STABLE"},
        status=200,
    )
    assert nsx_cluster.status(opts)["overall_status"] == "STABLE"


def test_transport_zone_list_and_get(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/transport-zones",
        json={"results": [{"id": "tz1"}]},
        status=200,
    )
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/transport-zones/tz1",
        json={"id": "tz1"},
        status=200,
    )
    assert nsx_transport_zone.list_(opts)["results"][0]["id"] == "tz1"
    assert nsx_transport_zone.get(opts, "tz1")["id"] == "tz1"


def test_transport_node_list(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/transport-nodes",
        json={"results": []},
        status=200,
    )
    assert nsx_transport_node.list_(opts) == {"results": []}


def test_compute_collection_list(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/fabric/compute-collections",
        json={"results": []},
        status=200,
    )
    assert nsx_compute_collection.list_(opts) == {"results": []}


def test_role_binding_lifecycle(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/aaa/role-bindings",
        json={"results": []},
        status=200,
    )
    mocked_responses.add(
        responses.POST,
        "https://nsx.test/api/v1/aaa/role-bindings",
        json={"id": "rb-1"},
        status=200,
    )
    mocked_responses.add(
        responses.DELETE, "https://nsx.test/api/v1/aaa/role-bindings/rb-1", status=200
    )
    nsx_role_binding.list_(opts)
    nsx_role_binding.create(opts, "alice", "remote_user", [{"role": "auditor"}])
    nsx_role_binding.delete(opts, "rb-1")
