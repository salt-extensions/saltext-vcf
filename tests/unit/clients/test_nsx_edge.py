"""Tests for the NSX edge-node client (``saltext.vcf.clients.nsx_edge``)."""

import pytest
import requests
import responses

from saltext.vcf.clients import nsx_edge


def test_list_sends_edgenode_query_param(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/transport-nodes",
        json={"results": [{"id": "edge-1", "node_deployment_info": {"resource_type": "EdgeNode"}}]},
        status=200,
        match=[responses.matchers.query_param_matcher({"node_types": "EdgeNode"})],
    )
    result = nsx_edge.list_(opts)
    assert result["results"][0]["id"] == "edge-1"


def test_get_returns_node(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/transport-nodes/edge-1",
        json={"id": "edge-1", "display_name": "edge-01"},
        status=200,
    )
    assert nsx_edge.get(opts, "edge-1") == {"id": "edge-1", "display_name": "edge-01"}


def test_get_or_none_returns_node(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/transport-nodes/edge-1",
        json={"id": "edge-1"},
        status=200,
    )
    assert nsx_edge.get_or_none(opts, "edge-1") == {"id": "edge-1"}


def test_get_or_none_returns_none_on_404(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/transport-nodes/missing",
        json={"error_message": "not found"},
        status=404,
    )
    assert nsx_edge.get_or_none(opts, "missing") is None


def test_get_or_none_reraises_non_404(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/transport-nodes/edge-boom",
        json={"error_message": "server error"},
        status=500,
    )
    with pytest.raises(requests.HTTPError):
        nsx_edge.get_or_none(opts, "edge-boom")


def test_create_posts_body(opts, mocked_responses):
    body = {
        "resource_type": "TransportNode",
        "display_name": "edge-01",
        "node_deployment_info": {"resource_type": "EdgeNode"},
    }
    mocked_responses.add(
        responses.POST,
        "https://nsx.test/api/v1/transport-nodes",
        json={"id": "edge-1", **body},
        status=200,
        match=[responses.matchers.json_params_matcher(body)],
    )
    assert nsx_edge.create(opts, body)["id"] == "edge-1"


def test_update_puts_body(opts, mocked_responses):
    body = {"display_name": "edge-01-renamed"}
    mocked_responses.add(
        responses.PUT,
        "https://nsx.test/api/v1/transport-nodes/edge-1",
        json={"id": "edge-1", **body},
        status=200,
        match=[responses.matchers.json_params_matcher(body)],
    )
    assert nsx_edge.update(opts, "edge-1", body)["display_name"] == "edge-01-renamed"


def test_delete_calls_delete(opts, mocked_responses):
    mocked_responses.add(
        responses.DELETE,
        "https://nsx.test/api/v1/transport-nodes/edge-1",
        status=200,
    )
    assert nsx_edge.delete(opts, "edge-1") == {}


def test_redeploy_sends_action_query_param(opts, mocked_responses):
    mocked_responses.add(
        responses.POST,
        "https://nsx.test/api/v1/transport-nodes/edge-1",
        json={"id": "edge-1", "state": "in_progress"},
        status=200,
        match=[responses.matchers.query_param_matcher({"action": "redeploy"})],
    )
    result = nsx_edge.redeploy(opts, "edge-1")
    assert result["state"] == "in_progress"


def test_state_returns_state(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/transport-nodes/edge-1/state",
        json={"state": "success"},
        status=200,
    )
    assert nsx_edge.state(opts, "edge-1") == {"state": "success"}


def test_cluster_allocation_status(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/edge-clusters/cluster-1/allocation-status",
        json={"allocation_status": [{"edge_node_id": "edge-1"}]},
        status=200,
    )
    result = nsx_edge.cluster_allocation_status(opts, "cluster-1")
    assert result["allocation_status"][0]["edge_node_id"] == "edge-1"
