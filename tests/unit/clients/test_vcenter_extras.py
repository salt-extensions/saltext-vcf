"""Tests for clients.vcenter_{datastore,network,storage_policy,appliance}."""

import responses

from saltext.vmware.clients import vcenter_appliance
from saltext.vmware.clients import vcenter_datastore
from saltext.vmware.clients import vcenter_network
from saltext.vmware.clients import vcenter_storage_policy


def test_datastore_list(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/datastore",
        json=[{"datastore": "ds-1", "name": "vsanDatastore"}],
        status=200,
    )
    assert vcenter_datastore.list_(opts) == [{"datastore": "ds-1", "name": "vsanDatastore"}]


def test_datastore_get(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/datastore/ds-1",
        json={"name": "vsanDatastore", "free_space": 12345},
        status=200,
    )
    assert vcenter_datastore.get(opts, "ds-1")["name"] == "vsanDatastore"


def test_network_list(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/network",
        json=[{"network": "n-1", "type": "DISTRIBUTED_PORTGROUP"}],
        status=200,
    )
    assert vcenter_network.list_(opts) == [{"network": "n-1", "type": "DISTRIBUTED_PORTGROUP"}]


def test_storage_policy_list_and_get(opts, vcenter_authed):
    """``get`` uses the filter query (?policies=<id>) since SPBM has no per-id GET."""
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/storage/policies",
        json=[{"policy": "p-1", "name": "vSAN Default"}],
        status=200,
    )
    # Second call is the filter-style get
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/storage/policies",
        json=[{"policy": "p-1", "name": "vSAN Default"}],
        status=200,
    )
    assert vcenter_storage_policy.list_(opts) == [{"policy": "p-1", "name": "vSAN Default"}]
    detail = vcenter_storage_policy.get(opts, "p-1")
    assert detail["name"] == "vSAN Default"
    # Confirm the second call used the filter query
    assert "policies=p-1" in vcenter_authed.calls[-1].request.url


def test_storage_policy_get_returns_404_when_empty(opts, vcenter_authed):
    """When the filter returns an empty list, get() raises 404."""
    import pytest
    import requests as r

    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/storage/policies",
        json=[],
        status=200,
    )
    with pytest.raises(r.HTTPError):
        vcenter_storage_policy.get(opts, "missing-id")


def test_storage_policy_get_or_none(opts, vcenter_authed):
    """get_or_none maps empty-list → None (the synthetic 404 in get())."""
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/storage/policies",
        json=[],
        status=200,
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/storage/policies",
        json=[{"policy": "p-1", "name": "Found"}],
        status=200,
    )
    assert vcenter_storage_policy.get_or_none(opts, "missing") is None
    assert vcenter_storage_policy.get_or_none(opts, "p-1")["name"] == "Found"


def test_appliance_services_dict_shape(opts, vcenter_authed):
    """Appliance services is a *dict* keyed by service name, not a list."""
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/appliance/services",
        json={"vmware-vpxd": {"state": "STARTED"}, "vsphere-ui": {"state": "STARTED"}},
        status=200,
    )
    result = vcenter_appliance.services_list(opts)
    assert isinstance(result, dict)
    assert "vmware-vpxd" in result


def test_appliance_services_action(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST, "https://vc.test/api/appliance/services/vmware-vpxd", status=204
    )
    vcenter_appliance.services_restart(opts, "vmware-vpxd")
    assert "action=restart" in vcenter_authed.calls[-1].request.url


def test_appliance_health_system_string(opts, vcenter_authed):
    """``/api/appliance/health/system`` returns a plain JSON string."""
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/appliance/health/system",
        json="green",
        status=200,
    )
    assert vcenter_appliance.health_system(opts) == "green"


def test_appliance_version(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/appliance/system/version",
        json={"product": "VMware vCenter Server", "build": "25397534"},
        status=200,
    )
    assert vcenter_appliance.version(opts)["product"] == "VMware vCenter Server"


def test_appliance_dns_get_and_set(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/appliance/networking/dns/servers",
        json={"mode": "is_static", "servers": ["10.0.0.1"]},
        status=200,
    )
    vcenter_authed.add(
        responses.PATCH,
        "https://vc.test/api/appliance/networking/dns/servers",
        status=204,
    )
    assert vcenter_appliance.dns_get(opts)["servers"] == ["10.0.0.1"]
    vcenter_appliance.dns_set(opts, ["10.0.0.2", "10.0.0.3"])
    import json

    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {"mode": "is_static", "servers": ["10.0.0.2", "10.0.0.3"]}


def test_appliance_logging_forwarding_get_set(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/appliance/logging/forwarding",
        json=[],
        status=200,
    )
    vcenter_authed.add(
        responses.PATCH,
        "https://vc.test/api/appliance/logging/forwarding",
        status=204,
    )
    assert vcenter_appliance.logging_forwarding_get(opts) == []
    vcenter_appliance.logging_forwarding_set(
        opts, [{"hostname": "c", "port": 514, "protocol": "UDP"}]
    )
