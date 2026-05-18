"""Tests for the NSX DFW exec modules."""

import pytest
import responses

from saltext.vcf.modules import vcf_nsx_context_profile
from saltext.vcf.modules import vcf_nsx_firewall_rule
from saltext.vcf.modules import vcf_nsx_security_policy
from saltext.vcf.modules import vcf_nsx_service


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    for mod in (
        vcf_nsx_security_policy,
        vcf_nsx_firewall_rule,
        vcf_nsx_service,
        vcf_nsx_context_profile,
    ):
        monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_security_policy_list(mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/policy/api/v1/infra/domains/default/security-policies",
        json={"results": []},
        status=200,
    )
    assert vcf_nsx_security_policy.list_() == {"results": []}


def test_firewall_rule_create(mocked_responses):
    mocked_responses.add(
        responses.PUT,
        "https://nsx.test/policy/api/v1/infra/domains/default/security-policies/sp/rules/r",
        json={"id": "r"},
        status=200,
    )
    vcf_nsx_firewall_rule.create("r", "sp", action="ALLOW")


def test_service_get(mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/policy/api/v1/infra/services/HTTPS",
        json={"id": "HTTPS"},
        status=200,
    )
    assert vcf_nsx_service.get("HTTPS")["id"] == "HTTPS"


def test_context_profile_list(mocked_responses):
    mocked_responses.add(
        responses.GET,
        "https://nsx.test/policy/api/v1/infra/context-profiles",
        json={"results": []},
        status=200,
    )
    assert vcf_nsx_context_profile.list_() == {"results": []}
