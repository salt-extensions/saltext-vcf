"""Tests for the vCenter datastore/network/storage_policy/appliance exec modules."""

import pytest
import responses

from saltext.vmware.modules import vmware_vcenter_appliance
from saltext.vmware.modules import vmware_vcenter_datastore
from saltext.vmware.modules import vmware_vcenter_network
from saltext.vmware.modules import vmware_vcenter_storage_policy


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    for mod in (
        vmware_vcenter_datastore,
        vmware_vcenter_network,
        vmware_vcenter_storage_policy,
        vmware_vcenter_appliance,
    ):
        monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_datastore_list_and_get(vcenter_authed):
    vcenter_authed.add(responses.GET, "https://vc.test/api/vcenter/datastore", json=[], status=200)
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/datastore/ds-1",
        json={"name": "ds"},
        status=200,
    )
    assert vmware_vcenter_datastore.list_() == []
    assert vmware_vcenter_datastore.get("ds-1") == {"name": "ds"}


def test_network_list(vcenter_authed):
    vcenter_authed.add(responses.GET, "https://vc.test/api/vcenter/network", json=[], status=200)
    assert vmware_vcenter_network.list_() == []


def test_storage_policy_get(vcenter_authed):
    """SPBM has no per-id GET — the client uses the filter pattern."""
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/storage/policies",
        json=[{"policy": "p-1", "name": "n"}],
        status=200,
    )
    assert vmware_vcenter_storage_policy.get("p-1")["name"] == "n"
    assert "policies=p-1" in vcenter_authed.calls[-1].request.url


def test_appliance_version(vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/appliance/system/version",
        json={"product": "vCenter"},
        status=200,
    )
    assert vmware_vcenter_appliance.version() == {"product": "vCenter"}


def test_appliance_services_start(vcenter_authed):
    vcenter_authed.add(
        responses.POST, "https://vc.test/api/appliance/services/vsphere-ui", status=204
    )
    vmware_vcenter_appliance.services_start("vsphere-ui")
    assert "action=start" in vcenter_authed.calls[-1].request.url
