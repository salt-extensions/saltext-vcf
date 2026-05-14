"""Framework-interface tests for resources.vcenter."""

import pytest
import responses

from saltext.vmware.resources import vcenter as vc

INSTANCES_KEY = vc.CONTEXT_KEY


def test_discover_returns_instance_ids(framework_opts):
    assert sorted(vc.discover(framework_opts)) == ["mgmt-vc", "prod-vc"]


def test_init_initialized_shutdown_cycle(monkeypatch, framework_opts):
    ctx = {}
    monkeypatch.setattr(vc, "__context__", ctx, raising=False)
    assert vc.initialized() is False
    vc.init(framework_opts)
    assert vc.initialized() is True
    assert "mgmt-vc" in ctx[INSTANCES_KEY]["instances"]
    vc.shutdown(framework_opts)
    assert INSTANCES_KEY not in ctx


def test_grains_for_current_resource(inject_resource_dunders, framework_opts):
    instances = framework_opts["pillar"]["resources"]["vcenter"]["instances"]
    inject_resource_dunders(vc, "mgmt-vc", INSTANCES_KEY, instances)
    g = vc.grains()
    assert g == {
        "resource_type": "vcenter",
        "resource_id": "mgmt-vc",
        "host": "vc.test",
    }


def test_ping_ok(inject_resource_dunders, framework_opts, mocked_responses):
    instances = framework_opts["pillar"]["resources"]["vcenter"]["instances"]
    inject_resource_dunders(vc, "mgmt-vc", INSTANCES_KEY, instances)
    mocked_responses.add(responses.POST, "https://vc.test/api/session", json="token", status=200)
    assert vc.ping() is True


def test_ping_unreachable(inject_resource_dunders, framework_opts, mocked_responses):
    instances = framework_opts["pillar"]["resources"]["vcenter"]["instances"]
    inject_resource_dunders(vc, "mgmt-vc", INSTANCES_KEY, instances)
    mocked_responses.add(responses.POST, "https://vc.test/api/session", status=401)
    assert vc.ping() is False


@pytest.mark.usefixtures("vcenter_authed")
def test_cluster_list_uses_current_resource(
    inject_resource_dunders, framework_opts, vcenter_authed
):
    instances = framework_opts["pillar"]["resources"]["vcenter"]["instances"]
    inject_resource_dunders(vc, "mgmt-vc", INSTANCES_KEY, instances)
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/cluster",
        json=[{"cluster": "c1"}],
        status=200,
    )
    assert vc.cluster_list() == [{"cluster": "c1"}]


def test_other_resource_id_targets_other_host(
    inject_resource_dunders, framework_opts, mocked_responses
):
    instances = framework_opts["pillar"]["resources"]["vcenter"]["instances"]
    inject_resource_dunders(vc, "prod-vc", INSTANCES_KEY, instances)
    mocked_responses.add(responses.POST, "https://prod-vc.test/api/session", json="t", status=200)
    mocked_responses.add(
        responses.GET, "https://prod-vc.test/api/vcenter/cluster", json=[], status=200
    )
    assert vc.cluster_list() == []


@pytest.mark.usefixtures("vcenter_authed")
def test_vks_ops_routed_to_current_resource(
    inject_resource_dunders, framework_opts, vcenter_authed
):
    instances = framework_opts["pillar"]["resources"]["vcenter"]["instances"]
    inject_resource_dunders(vc, "mgmt-vc", INSTANCES_KEY, instances)
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/namespace-management/supervisor-services",
        json=[{"supervisor_service": "tkg"}],
        status=200,
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/namespace-management/virtual-machine-classes",
        json=[{"id": "guaranteed-small"}],
        status=200,
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/namespace-management/cluster-size-info",
        json={"TINY": {}},
        status=200,
    )
    assert vc.supervisor_service_list()[0]["supervisor_service"] == "tkg"
    assert vc.vm_class_list()[0]["id"] == "guaranteed-small"
    assert "TINY" in vc.supervisor_size_info()


def test_vm_search_tree_summary_route(inject_resource_dunders, framework_opts, vcenter_authed):
    instances = framework_opts["pillar"]["resources"]["vcenter"]["instances"]
    inject_resource_dunders(vc, "mgmt-vc", INSTANCES_KEY, instances)
    # search
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/vm",
        json=[{"vm": "vm-1", "power_state": "POWERED_ON"}],
        status=200,
    )
    out = vc.vm_search(power_states=["POWERED_ON"])
    assert out[0]["vm"] == "vm-1"
    assert "power_states=POWERED_ON" in vcenter_authed.calls[-1].request.url
    # summary (single list call)
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/vm",
        json=[{"vm": "vm-1", "power_state": "POWERED_ON"}],
        status=200,
    )
    assert vc.vm_summary()["total"] == 1
    # tree (4 endpoints)
    for endpoint in ("datacenter", "cluster", "host", "vm"):
        vcenter_authed.add(
            responses.GET, f"https://vc.test/api/vcenter/{endpoint}", json=[], status=200
        )
    assert vc.vm_tree() == {}
