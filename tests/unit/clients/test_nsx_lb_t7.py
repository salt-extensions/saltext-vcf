"""Tests for the NSX Load Balancer clients (T7)."""

import json

import responses

from saltext.vmware.clients import nsx_lb_app_profile
from saltext.vmware.clients import nsx_lb_monitor
from saltext.vmware.clients import nsx_lb_persistence
from saltext.vmware.clients import nsx_lb_pool
from saltext.vmware.clients import nsx_lb_service
from saltext.vmware.clients import nsx_lb_virtual_server

BASE = "https://nsx.test"
INFRA = f"{BASE}/policy/api/v1/infra"


def test_lb_service_list_get_create_delete(opts, mocked_responses):
    mocked_responses.add(responses.GET, f"{INFRA}/lb-services", json={"results": []}, status=200)
    mocked_responses.add(
        responses.GET, f"{INFRA}/lb-services/svc-1", json={"id": "svc-1"}, status=200
    )
    mocked_responses.add(
        responses.PUT, f"{INFRA}/lb-services/svc-1", json={"id": "svc-1"}, status=200
    )
    mocked_responses.add(responses.DELETE, f"{INFRA}/lb-services/svc-1", json=None, status=200)

    assert nsx_lb_service.list_(opts) == {"results": []}
    assert nsx_lb_service.get(opts, "svc-1")["id"] == "svc-1"
    nsx_lb_service.create(opts, "svc-1", size="SMALL", connectivity_path="/infra/tier-1s/t1")
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["display_name"] == "svc-1"
    assert body["size"] == "SMALL"
    nsx_lb_service.delete(opts, "svc-1")


def test_lb_service_get_or_none_404(opts, mocked_responses):
    mocked_responses.add(responses.GET, f"{INFRA}/lb-services/missing", status=404)
    assert nsx_lb_service.get_or_none(opts, "missing") is None


def test_lb_virtual_server_crud(opts, mocked_responses):
    mocked_responses.add(
        responses.GET, f"{INFRA}/lb-virtual-servers", json={"results": []}, status=200
    )
    mocked_responses.add(
        responses.PUT, f"{INFRA}/lb-virtual-servers/vs-1", json={"id": "vs-1"}, status=200
    )
    nsx_lb_virtual_server.list_(opts)
    nsx_lb_virtual_server.create(opts, "vs-1", ip_address="10.0.0.1", ports=["80"])
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["display_name"] == "vs-1"
    assert body["ip_address"] == "10.0.0.1"


def test_lb_virtual_server_get_or_none_404(opts, mocked_responses):
    mocked_responses.add(responses.GET, f"{INFRA}/lb-virtual-servers/missing", status=404)
    assert nsx_lb_virtual_server.get_or_none(opts, "missing") is None


def test_lb_pool_crud(opts, mocked_responses):
    mocked_responses.add(responses.GET, f"{INFRA}/lb-pools", json={"results": []}, status=200)
    mocked_responses.add(
        responses.PUT, f"{INFRA}/lb-pools/pool-1", json={"id": "pool-1"}, status=200
    )
    nsx_lb_pool.list_(opts)
    nsx_lb_pool.create(
        opts, "pool-1", members=[{"ip_address": "10.0.0.2"}], algorithm="ROUND_ROBIN"
    )
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["members"][0]["ip_address"] == "10.0.0.2"
    assert body["algorithm"] == "ROUND_ROBIN"


def test_lb_pool_get_or_none_404(opts, mocked_responses):
    mocked_responses.add(responses.GET, f"{INFRA}/lb-pools/missing", status=404)
    assert nsx_lb_pool.get_or_none(opts, "missing") is None


def test_lb_monitor_create_with_resource_type(opts, mocked_responses):
    mocked_responses.add(
        responses.PUT, f"{INFRA}/lb-monitor-profiles/m-1", json={"id": "m-1"}, status=200
    )
    nsx_lb_monitor.create(opts, "m-1", "LBHttpMonitorProfile", request_url="/healthz")
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["resource_type"] == "LBHttpMonitorProfile"
    assert body["request_url"] == "/healthz"


def test_lb_monitor_get_or_none_404(opts, mocked_responses):
    mocked_responses.add(responses.GET, f"{INFRA}/lb-monitor-profiles/missing", status=404)
    assert nsx_lb_monitor.get_or_none(opts, "missing") is None


def test_lb_app_profile_create(opts, mocked_responses):
    mocked_responses.add(
        responses.PUT, f"{INFRA}/lb-app-profiles/ap-1", json={"id": "ap-1"}, status=200
    )
    nsx_lb_app_profile.create(opts, "ap-1", "LBHttpProfile", x_forwarded_for="INSERT")
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["resource_type"] == "LBHttpProfile"
    assert body["x_forwarded_for"] == "INSERT"


def test_lb_app_profile_get_or_none_404(opts, mocked_responses):
    mocked_responses.add(responses.GET, f"{INFRA}/lb-app-profiles/missing", status=404)
    assert nsx_lb_app_profile.get_or_none(opts, "missing") is None


def test_lb_persistence_create(opts, mocked_responses):
    mocked_responses.add(
        responses.PUT, f"{INFRA}/lb-persistence-profiles/p-1", json={"id": "p-1"}, status=200
    )
    nsx_lb_persistence.create(opts, "p-1", "LBSourceIpPersistenceProfile", timeout=180)
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["resource_type"] == "LBSourceIpPersistenceProfile"
    assert body["timeout"] == 180


def test_lb_persistence_get_or_none_404(opts, mocked_responses):
    mocked_responses.add(responses.GET, f"{INFRA}/lb-persistence-profiles/missing", status=404)
    assert nsx_lb_persistence.get_or_none(opts, "missing") is None


def test_module_wrappers_delegate(opts, monkeypatch, mocked_responses):
    from saltext.vmware.modules import vmware_nsx_lb

    monkeypatch.setattr(vmware_nsx_lb, "__opts__", opts, raising=False)

    mocked_responses.add(responses.GET, f"{INFRA}/lb-services", json={"results": []}, status=200)
    mocked_responses.add(responses.PUT, f"{INFRA}/lb-pools/p-1", json={"id": "p-1"}, status=200)
    assert vmware_nsx_lb.list_services() == {"results": []}
    vmware_nsx_lb.create_pool("p-1", algorithm="LEAST_CONNECTION")
    body = json.loads(mocked_responses.calls[-1].request.body)
    assert body["algorithm"] == "LEAST_CONNECTION"
