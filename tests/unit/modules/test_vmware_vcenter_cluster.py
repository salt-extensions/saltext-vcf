"""Tests for modules.vmware_vcenter_cluster."""

import pytest
import responses

from saltext.vmware.modules import vmware_vcenter_cluster as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_list(vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/cluster",
        json=[{"cluster": "c1", "name": "Cluster1"}],
        status=200,
    )
    assert mod.list_() == [{"cluster": "c1", "name": "Cluster1"}]


def test_get(vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/cluster/c1",
        json={"name": "Cluster1"},
        status=200,
    )
    assert mod.get("c1") == {"name": "Cluster1"}


def test_create(vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/vcenter/cluster",
        json="c-new",
        status=200,
    )
    assert mod.create("Cluster1", datacenter="dc1") == "c-new"


def test_delete_empty_body(vcenter_authed):
    vcenter_authed.add(
        responses.DELETE,
        "https://vc.test/api/vcenter/cluster/c1",
        status=204,
    )
    assert mod.delete("c1") == {}


def test_get_404_propagates(vcenter_authed):
    import requests

    vcenter_authed.add(responses.GET, "https://vc.test/api/vcenter/cluster/missing", status=404)
    with pytest.raises(requests.HTTPError):
        mod.get("missing")
