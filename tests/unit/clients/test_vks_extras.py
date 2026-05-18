"""Tests for the VKS-extension clients (services catalog, vm classes, software, compat, kubeconfig)."""

import responses

from saltext.vcf.clients import vcenter_supervisor_compat
from saltext.vcf.clients import vcenter_supervisor_kubeconfig
from saltext.vcf.clients import vcenter_supervisor_service
from saltext.vcf.clients import vcenter_supervisor_software
from saltext.vcf.clients import vcenter_vm_class


def test_supervisor_service_list_get_versions(opts, vcenter_authed):
    base = "https://vc.test/api/vcenter/namespace-management/supervisor-services"
    vcenter_authed.add(
        responses.GET,
        base,
        json=[{"supervisor_service": "tkg.vsphere.vmware.com", "state": "ACTIVATED"}],
        status=200,
    )
    vcenter_authed.add(responses.GET, f"{base}/tkg", json={"state": "ACTIVATED"}, status=200)
    vcenter_authed.add(responses.GET, f"{base}/tkg/versions", json=["v1.0", "v2.0"], status=200)
    assert vcenter_supervisor_service.list_(opts)[0]["state"] == "ACTIVATED"
    assert vcenter_supervisor_service.get(opts, "tkg")["state"] == "ACTIVATED"
    assert vcenter_supervisor_service.list_versions(opts, "tkg") == ["v1.0", "v2.0"]


def test_supervisor_service_lifecycle(opts, vcenter_authed):
    base = "https://vc.test/api/vcenter/namespace-management/supervisor-services"
    vcenter_authed.add(responses.POST, base, json={}, status=200)
    vcenter_authed.add(responses.POST, f"{base}/tkg", json={}, status=200)
    vcenter_authed.add(responses.DELETE, f"{base}/tkg", status=200)
    vcenter_supervisor_service.create(opts, {"supervisor_service": "tkg"})
    vcenter_supervisor_service.activate(opts, "tkg")
    vcenter_supervisor_service.deactivate(opts, "tkg")
    vcenter_supervisor_service.delete(opts, "tkg")


def test_supervisor_service_get_or_none(opts, vcenter_authed):
    base = "https://vc.test/api/vcenter/namespace-management/supervisor-services"
    vcenter_authed.add(responses.GET, f"{base}/missing", status=404)
    assert vcenter_supervisor_service.get_or_none(opts, "missing") is None


def test_vm_class_crud(opts, vcenter_authed):
    base = "https://vc.test/api/vcenter/namespace-management/virtual-machine-classes"
    vcenter_authed.add(
        responses.GET,
        base,
        json=[{"id": "guaranteed-small", "cpu_count": 2, "memory_MB": 4096}],
        status=200,
    )
    vcenter_authed.add(
        responses.GET,
        f"{base}/guaranteed-small",
        json={"id": "guaranteed-small"},
        status=200,
    )
    vcenter_authed.add(responses.GET, f"{base}/missing", status=404)
    vcenter_authed.add(responses.POST, base, json={}, status=200)
    vcenter_authed.add(responses.PATCH, f"{base}/my", json={}, status=200)
    vcenter_authed.add(responses.DELETE, f"{base}/my", status=200)
    assert vcenter_vm_class.list_(opts)[0]["id"] == "guaranteed-small"
    assert vcenter_vm_class.get(opts, "guaranteed-small")["id"] == "guaranteed-small"
    assert vcenter_vm_class.get_or_none(opts, "missing") is None
    vcenter_vm_class.create(opts, {"id": "my", "cpu_count": 1, "memory_MB": 1024})
    vcenter_vm_class.update(opts, "my", {"cpu_count": 2})
    vcenter_vm_class.delete(opts, "my")


def test_supervisor_software_list_get_upgrade(opts, vcenter_authed):
    base = "https://vc.test/api/vcenter/namespace-management/software/clusters"
    vcenter_authed.add(responses.GET, base, json=[], status=200)
    vcenter_authed.add(responses.GET, f"{base}/c1", json={"current_version": "v1"}, status=200)
    vcenter_authed.add(responses.GET, f"{base}/missing", status=404)
    vcenter_authed.add(responses.POST, f"{base}/c1", json={}, status=200)
    assert vcenter_supervisor_software.list_(opts) == []
    assert vcenter_supervisor_software.get(opts, "c1")["current_version"] == "v1"
    assert vcenter_supervisor_software.get_or_none(opts, "missing") is None
    vcenter_supervisor_software.upgrade(opts, "c1", {"desired_version": "v2"})


def test_supervisor_compat_helpers(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/namespace-management/cluster-compatibility",
        json=[{"cluster": "c1", "compatible": True}],
        status=200,
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/namespace-management/distributed-switch-compatibility",
        json=[{"compatible": False}],
        status=200,
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/namespace-management/edge-cluster-compatibility",
        json=[],
        status=200,
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/namespace-management/cluster-size-info",
        json={"TINY": {}, "SMALL": {}},
        status=200,
    )
    assert vcenter_supervisor_compat.list_cluster_compatibility(opts)[0]["compatible"] is True
    assert vcenter_supervisor_compat.list_dvs_compatibility(opts, "c1")[0]["compatible"] is False
    assert vcenter_supervisor_compat.list_edge_cluster_compatibility(opts, "c1", "dvs1") == []
    assert "TINY" in vcenter_supervisor_compat.get_cluster_size_info(opts)


def test_kubeconfig_cluster_path(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/namespace-management/clusters/c1/kubeconfig",
        json={"kube_config": "yaml-body"},
        status=200,
    )
    assert vcenter_supervisor_kubeconfig.get_kubeconfig(opts, "c1") == "yaml-body"


def test_kubeconfig_falls_back_to_user_path(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/namespace-management/clusters/c1/kubeconfig",
        status=404,
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/namespaces/user/kubeconfig",
        json={"kube_config": "fallback-yaml"},
        status=200,
    )
    assert vcenter_supervisor_kubeconfig.get_kubeconfig(opts, "c1") == "fallback-yaml"


def test_kubeconfig_for_namespace(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/namespaces/user/kubeconfig",
        json={"kube_config": "ns-scoped"},
        status=200,
    )
    assert vcenter_supervisor_kubeconfig.get_kubeconfig_for_namespace(opts, "ns1") == "ns-scoped"
