"""Tests for the VCF Operations client modules."""

import responses

from saltext.vcf.clients import vcfops_adapter
from saltext.vcf.clients import vcfops_alert
from saltext.vcf.clients import vcfops_policy
from saltext.vcf.clients import vcfops_resource
from saltext.vcf.clients import vcfops_version


def test_version(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/versions",
        json={"values": []},
        status=200,
    )
    assert vcfops_version.get(opts) == {"values": []}


def test_resource_list_pagination_params(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/resources",
        json={"pageInfo": {}, "resourceList": []},
        status=200,
    )
    vcfops_resource.list_(opts, page=2, page_size=50, resourceKind="VirtualMachine")
    url = vcfops_authed.calls[-1].request.url
    assert "page=2" in url and "pageSize=50" in url and "resourceKind=VirtualMachine" in url


def test_resource_get(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/resources/r-1",
        json={"identifier": "r-1"},
        status=200,
    )
    assert vcfops_resource.get(opts, "r-1") == {"identifier": "r-1"}


def test_resource_relationships_and_stats(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/resources/r-1/relationships",
        json={"relations": []},
        status=200,
    )
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/resources/r-1/stats",
        json={"values": []},
        status=200,
    )
    assert vcfops_resource.relationships(opts, "r-1") == {"relations": []}
    assert vcfops_resource.stats(opts, "r-1") == {"values": []}


def test_adapter_list_and_get(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/adapterkinds",
        json={"adapter-kind": []},
        status=200,
    )
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/adapterkinds/VMWARE",
        json={"key": "VMWARE"},
        status=200,
    )
    vcfops_adapter.list_(opts)
    assert vcfops_adapter.get(opts, "VMWARE")["key"] == "VMWARE"


def test_alerts_list(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/alertdefinitions",
        json={"alertDefinitions": []},
        status=200,
    )
    assert vcfops_alert.alerts_list(opts) == {"alertDefinitions": []}


def test_policy_list_and_get(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/policies",
        json={"policies": [{"id": "p1"}]},
        status=200,
    )
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/policies/p1",
        json={"id": "p1"},
        status=200,
    )
    vcfops_policy.list_(opts)
    assert vcfops_policy.get(opts, "p1")["id"] == "p1"


def test_notification_rules(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/notifications/rules",
        json={"notification-rule": []},
        status=200,
    )
    assert vcfops_policy.notification_rules_list(opts) == {"notification-rule": []}
