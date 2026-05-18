"""Tests for the NSX DFW clients: security_policy, firewall_rule, service, context_profile."""

import json

import responses

from saltext.vcf.clients import nsx_context_profile
from saltext.vcf.clients import nsx_firewall_rule
from saltext.vcf.clients import nsx_security_policy
from saltext.vcf.clients import nsx_service


def test_security_policy_list(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/policy/api/v1/infra/domains/default/security-policies",
        json={"results": []},
        status=200,
    )
    assert nsx_security_policy.list_(opts) == {"results": []}


def test_security_policy_create_uses_put(opts, mocked_responses):
    mocked_responses.add(
        responses.PUT,
        "https://nsx.test/policy/api/v1/infra/domains/default/security-policies/sp-a",
        json={"id": "sp-a"},
        status=200,
    )
    nsx_security_policy.create(opts, "sp-a", category="Application")
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["display_name"] == "sp-a"
    assert body["category"] == "Application"


def test_security_policy_custom_domain(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/policy/api/v1/infra/domains/tenant-1/security-policies/sp-1",
        json={"id": "sp-1"},
        status=200,
    )
    assert nsx_security_policy.get(opts, "sp-1", domain="tenant-1")["id"] == "sp-1"


def test_firewall_rule_list(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/policy/api/v1/infra/domains/default/security-policies/sp-a/rules",
        json={"results": []},
        status=200,
    )
    assert nsx_firewall_rule.list_(opts, "sp-a") == {"results": []}


def test_firewall_rule_create(opts, mocked_responses):
    mocked_responses.add(
        responses.PUT,
        "https://nsx.test/policy/api/v1/infra/domains/default/security-policies/sp-a/rules/r1",
        json={"id": "r1"},
        status=200,
    )
    nsx_firewall_rule.create(
        opts,
        "r1",
        "sp-a",
        source_groups=["/infra/domains/default/groups/g1"],
        destination_groups=["/infra/domains/default/groups/g2"],
        action="ALLOW",
        services=["/infra/services/HTTPS"],
    )
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["action"] == "ALLOW"
    assert body["display_name"] == "r1"


def test_firewall_rule_delete(opts, mocked_responses):
    mocked_responses.add(
        responses.DELETE,
        "https://nsx.test/policy/api/v1/infra/domains/default/security-policies/sp-a/rules/r1",
        status=200,
    )
    assert nsx_firewall_rule.delete(opts, "r1", "sp-a") == {}


def test_service_list_and_get(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/policy/api/v1/infra/services",
        json={"results": [{"id": "HTTPS"}]},
        status=200,
    )
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/policy/api/v1/infra/services/HTTPS",
        json={"id": "HTTPS"},
        status=200,
    )
    assert nsx_service.list_(opts)["results"][0]["id"] == "HTTPS"
    assert nsx_service.get(opts, "HTTPS")["id"] == "HTTPS"


def test_service_create_put(opts, mocked_responses):
    mocked_responses.add(
        responses.PUT,
        "https://nsx.test/policy/api/v1/infra/services/MYSVC",
        json={"id": "MYSVC"},
        status=200,
    )
    nsx_service.create(
        opts,
        "MYSVC",
        service_entries=[
            {
                "resource_type": "L4PortSetServiceEntry",
                "l4_protocol": "TCP",
                "destination_ports": ["8080"],
            }
        ],
    )
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["service_entries"][0]["destination_ports"] == ["8080"]


def test_context_profile_list(opts, mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/policy/api/v1/infra/context-profiles",
        json={"results": []},
        status=200,
    )
    assert nsx_context_profile.list_(opts) == {"results": []}
