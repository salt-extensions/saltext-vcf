"""Tests for the NSX cluster client (status + API VIP)."""

import responses

from saltext.vcf.clients import nsx_cluster


def test_cluster_status(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/cluster/status",
        json={"overall_status": "STABLE"},
        status=200,
    )
    assert nsx_cluster.status(opts)["overall_status"] == "STABLE"


def test_api_virtual_ip_get(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/api/v1/cluster/api-virtual-ip",
        json={"ip_address": "10.0.0.5"},
        status=200,
    )
    assert nsx_cluster.api_virtual_ip_get(opts)["ip_address"] == "10.0.0.5"


def test_api_virtual_ip_set_sends_query_params(opts, mocked_responses):
    mocked_responses.add(
        responses.POST,
        "https://nsx.test/api/v1/cluster/api-virtual-ip",
        json={"ip_address": "10.0.0.5"},
        status=200,
        match=[
            responses.matchers.query_param_matcher(
                {"action": "set_virtual_ip", "ip_address": "10.0.0.5"}
            )
        ],
    )
    result = nsx_cluster.api_virtual_ip_set(opts, "10.0.0.5")
    assert result["ip_address"] == "10.0.0.5"


def test_api_virtual_ip_clear_sends_action(opts, mocked_responses):
    mocked_responses.add(
        responses.POST,
        "https://nsx.test/api/v1/cluster/api-virtual-ip",
        json={"ip_address": ""},
        status=200,
        match=[responses.matchers.query_param_matcher({"action": "clear_virtual_ip"})],
    )
    result = nsx_cluster.api_virtual_ip_clear(opts)
    assert result["ip_address"] == ""
