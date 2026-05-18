"""Tests for the Batch 5 NSX polish clients."""

import json

import responses

from saltext.vcf.clients import nsx_dhcp
from saltext.vcf.clients import nsx_edge_cluster
from saltext.vcf.clients import nsx_ip_block
from saltext.vcf.clients import nsx_ip_pool
from saltext.vcf.clients import nsx_nat


def test_nat_list_uses_t1_scope(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/policy/api/v1/infra/tier-1s/t1-a/nat/USER/nat-rules",
        json={"results": []},
        status=200,
    )
    assert nsx_nat.list_(opts, "t1-a") == {"results": []}


def test_nat_create_put(opts, mocked_responses):
    mocked_responses.add(
        responses.PUT,
        "https://nsx.test/policy/api/v1/infra/tier-1s/t1-a/nat/USER/nat-rules/r1",
        json={"id": "r1"},
        status=200,
    )
    nsx_nat.create(opts, "r1", "t1-a", action="DNAT", destination_network="1.2.3.4")
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["action"] == "DNAT"


def test_ip_block_create(opts, mocked_responses):
    mocked_responses.add(
        responses.PUT,
        "https://nsx.test/policy/api/v1/infra/ip-blocks/b1",
        json={"id": "b1"},
        status=200,
    )
    nsx_ip_block.create(opts, "b1", "10.0.0.0/16")
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["cidr"] == "10.0.0.0/16"


def test_ip_pool_subnets_and_allocations(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/policy/api/v1/infra/ip-pools/p1/ip-subnets",
        json={"results": []},
        status=200,
    )
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/policy/api/v1/infra/ip-pools/p1/ip-allocations",
        json={"results": []},
        status=200,
    )
    assert nsx_ip_pool.list_subnets(opts, "p1") == {"results": []}
    assert nsx_ip_pool.list_allocations(opts, "p1") == {"results": []}


def test_edge_cluster_list_and_state(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/edge-clusters",
        json={"results": []},
        status=200,
    )
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/edge-clusters/ec1/state",
        json={"state": "stable"},
        status=200,
    )
    assert nsx_edge_cluster.list_(opts) == {"results": []}
    assert nsx_edge_cluster.state(opts, "ec1") == {"state": "stable"}


def test_dhcp_server_create(opts, mocked_responses):
    mocked_responses.add(
        responses.PUT,
        "https://nsx.test/policy/api/v1/infra/dhcp-server-configs/d1",
        json={"id": "d1"},
        status=200,
    )
    nsx_dhcp.server_create(opts, "d1", server_address="10.0.0.1/24")


def test_dhcp_relay_create(opts, mocked_responses):
    mocked_responses.add(
        responses.PUT,
        "https://nsx.test/policy/api/v1/infra/dhcp-relay-configs/r1",
        json={"id": "r1"},
        status=200,
    )
    nsx_dhcp.relay_create(opts, "r1", ["10.99.0.5", "10.99.0.6"])
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["server_addresses"] == ["10.99.0.5", "10.99.0.6"]
