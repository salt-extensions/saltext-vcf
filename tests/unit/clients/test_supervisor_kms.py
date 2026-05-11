"""Tests for clients.vcenter_supervisor + clients.vcenter_kms."""

import responses

from saltext.vmware.clients import vcenter_kms
from saltext.vmware.clients import vcenter_supervisor


def test_supervisor_list_clusters(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/namespace-management/clusters",
        json=[],
        status=200,
    )
    assert vcenter_supervisor.list_clusters(opts) == []


def test_supervisor_compatibility(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/namespace-management/cluster-compatibility",
        json=[{"cluster": "domain-c9", "compatible": True}],
        status=200,
    )
    result = vcenter_supervisor.list_compatibility(opts)
    assert result[0]["compatible"] is True


def test_supervisor_namespace_lifecycle(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/namespaces/instances",
        json=[],
        status=200,
    )
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/vcenter/namespaces/instances",
        json={"namespace": "ns1"},
        status=200,
    )
    vcenter_authed.add(
        responses.DELETE,
        "https://vc.test/api/vcenter/namespaces/instances/ns1",
        status=200,
    )
    assert vcenter_supervisor.list_namespaces(opts) == []
    vcenter_supervisor.create_namespace(opts, {"namespace": "ns1"})
    vcenter_supervisor.delete_namespace(opts, "ns1")


def test_kms_list_and_get_or_none(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/crypto-manager/kms/providers",
        json=[],
        status=200,
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/crypto-manager/kms/providers/missing",
        status=404,
    )
    assert vcenter_kms.list_(opts) == []
    assert vcenter_kms.get_or_none(opts, "missing") is None
