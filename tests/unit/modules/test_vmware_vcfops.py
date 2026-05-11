"""Tests for the VCF Operations exec modules."""

import pytest
import responses

from saltext.vmware.modules import vmware_vcfops_adapter
from saltext.vmware.modules import vmware_vcfops_alert
from saltext.vmware.modules import vmware_vcfops_policy
from saltext.vmware.modules import vmware_vcfops_resource
from saltext.vmware.modules import vmware_vcfops_version


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    for mod in (
        vmware_vcfops_version,
        vmware_vcfops_resource,
        vmware_vcfops_adapter,
        vmware_vcfops_alert,
        vmware_vcfops_policy,
    ):
        monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_version(vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/versions",
        json={"values": []},
        status=200,
    )
    assert vmware_vcfops_version.get() == {"values": []}


def test_resource_list(vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/resources",
        json={"resourceList": []},
        status=200,
    )
    assert vmware_vcfops_resource.list_(page=0, page_size=10) == {"resourceList": []}


def test_adapter_list(vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/adapterkinds",
        json={},
        status=200,
    )
    vmware_vcfops_adapter.list_()


def test_alerts_list(vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/alertdefinitions",
        json={"alertDefinitions": []},
        status=200,
    )
    vmware_vcfops_alert.alerts_list()


def test_policy_list(vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/policies",
        json={"policies": []},
        status=200,
    )
    vmware_vcfops_policy.list_()
