"""Tests for vcenter_vm search/tree/summary (A4 — VM filter/tree/summary)."""

import responses

from saltext.vmware.clients import vcenter_vm


def test_search_no_filters_omits_params(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/vm",
        json=[{"vm": "vm-1"}],
        status=200,
    )
    assert vcenter_vm.search(opts) == [{"vm": "vm-1"}]
    assert "filter." not in vcenter_authed.calls[-1].request.url


def test_search_power_state_single(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/vm",
        json=[{"vm": "vm-1", "power_state": "POWERED_ON"}],
        status=200,
    )
    out = vcenter_vm.search(opts, power_states=["POWERED_ON"])
    assert out[0]["power_state"] == "POWERED_ON"
    assert "power_states=POWERED_ON" in vcenter_authed.calls[-1].request.url


def test_search_power_state_multi_emits_repeated_keys(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/vm",
        json=[],
        status=200,
    )
    vcenter_vm.search(opts, power_states=["POWERED_ON", "SUSPENDED"])
    url = vcenter_authed.calls[-1].request.url
    assert "power_states=POWERED_ON" in url
    assert "power_states=SUSPENDED" in url


def test_search_multi_filter(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/vm",
        json=[],
        status=200,
    )
    vcenter_vm.search(opts, hosts=["h-1"], clusters=["c-1"], names=["alpha"])
    url = vcenter_authed.calls[-1].request.url
    assert "hosts=h-1" in url
    assert "clusters=c-1" in url
    assert "names=alpha" in url


def test_tree_composes(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/datacenter",
        json=[{"datacenter": "dc-1", "name": "DC"}],
        status=200,
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/cluster",
        json=[{"cluster": "cl-1", "name": "Cluster", "datacenter": "dc-1"}],
        status=200,
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/host",
        json=[{"host": "h-1", "name": "esx-1", "cluster": "cl-1"}],
        status=200,
    )
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/vm",
        json=[{"vm": "vm-1", "name": "alpha", "host": "h-1", "power_state": "POWERED_ON"}],
        status=200,
    )
    tree = vcenter_vm.tree(opts)
    assert tree["dc-1"]["name"] == "DC"
    cl = tree["dc-1"]["clusters"]["cl-1"]
    assert cl["name"] == "Cluster"
    host_bucket = cl["hosts"]["h-1"]
    assert host_bucket["name"] == "esx-1"
    assert host_bucket["vms"][0]["vm"] == "vm-1"


def test_tree_unbound_vm(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, "https://vc.test/api/vcenter/datacenter", json=[], status=200)
    vcenter_authed.add(responses.GET, "https://vc.test/api/vcenter/cluster", json=[], status=200)
    vcenter_authed.add(responses.GET, "https://vc.test/api/vcenter/host", json=[], status=200)
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/vm",
        json=[{"vm": "vm-templ", "name": "template", "power_state": "POWERED_OFF"}],
        status=200,
    )
    tree = vcenter_vm.tree(opts)
    # Unbound VM lands in datacenter=None, cluster=None, host="__unbound__"
    assert tree[None]["clusters"][None]["hosts"]["__unbound__"]["vms"][0]["vm"] == "vm-templ"


def test_summary_counts(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/vm",
        json=[
            {"vm": "vm-1", "power_state": "POWERED_ON", "cpu_count": 2, "memory_size_MiB": 1024},
            {"vm": "vm-2", "power_state": "POWERED_ON", "cpu_count": 4, "memory_size_MiB": 2048},
            {"vm": "vm-3", "power_state": "POWERED_OFF", "cpu_count": 2, "memory_size_MiB": 512},
        ],
        status=200,
    )
    s = vcenter_vm.summary(opts)
    assert s["total"] == 3
    assert s["by_power_state"] == {"POWERED_ON": 2, "POWERED_OFF": 1}
    assert s["by_cpu_count"] == {2: 2, 4: 1}
    assert s["total_memory_MiB"] == 1024 + 2048 + 512


def test_summary_empty(opts, vcenter_authed):
    vcenter_authed.add(responses.GET, "https://vc.test/api/vcenter/vm", json=[], status=200)
    s = vcenter_vm.summary(opts)
    assert s == {
        "total": 0,
        "by_power_state": {},
        "by_cpu_count": {},
        "total_memory_MiB": 0,
    }
