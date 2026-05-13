"""Tests for clients.vim_drs_rule (SOAP, cluster reconfigure)."""

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vmware.clients import vim_drs_rule


def _make_rule(
    kind,
    name,
    key=1,
    enabled=True,
    mandatory=False,
    vm_moids=None,
    vm_group=None,
    affine_host=None,
    anti_affine_host=None,
):
    if kind == "vm-affinity":
        rule = vim.cluster.AffinityRuleSpec()
    elif kind == "vm-anti-affinity":
        rule = vim.cluster.AntiAffinityRuleSpec()
    elif kind == "vm-host":
        rule = vim.cluster.VmHostRuleInfo()
    else:
        raise ValueError(kind)
    rule.key = key
    rule.name = name
    rule.enabled = enabled
    rule.mandatory = mandatory
    if vm_moids is not None and hasattr(rule, "vm"):
        rule.vm = [_moref(m) for m in vm_moids]
    if vm_group is not None:
        rule.vmGroupName = vm_group
    if affine_host is not None:
        rule.affineHostGroupName = affine_host
    if anti_affine_host is not None:
        rule.antiAffineHostGroupName = anti_affine_host
    return rule


def _moref(moid):
    # Real pyVmomi reference; passes type-checking on rule specs.
    return vim.VirtualMachine(moid, None)


def _host_moref(moid):
    return vim.HostSystem(moid, None)


def _fake_cluster(rules=None, groups=None):
    cl = MagicMock()
    cl.configurationEx.rule = rules or []
    cl.configurationEx.group = groups or []
    cl.ReconfigureComputeResource_Task.return_value = MagicMock(_moId="task-1")
    return cl


@pytest.fixture
def cluster_factory(monkeypatch):
    holder = {"cluster": _fake_cluster()}

    def get_cluster(opts, name, profile=None):
        return holder["cluster"]

    monkeypatch.setattr(vim_drs_rule, "_cluster", get_cluster)
    return holder


def test_list_returns_dicts(cluster_factory, opts):
    cluster_factory["cluster"] = _fake_cluster(
        rules=[
            _make_rule("vm-affinity", "keep-pair", key=1, vm_moids=["vm-1", "vm-2"]),
            _make_rule("vm-anti-affinity", "split", key=2, vm_moids=["vm-3", "vm-4"]),
            _make_rule("vm-host", "pin", key=3, vm_group="prod-vms", affine_host="prod-hosts"),
        ]
    )
    result = vim_drs_rule.list_(opts, "domain-c9")
    names = {r["name"] for r in result}
    assert names == {"keep-pair", "split", "pin"}
    affinity = next(r for r in result if r["name"] == "keep-pair")
    assert affinity["kind"] == "vm-affinity"
    assert affinity["vm_moids"] == ["vm-1", "vm-2"]
    pin = next(r for r in result if r["name"] == "pin")
    assert pin["kind"] == "vm-host"
    assert pin["vm_group_name"] == "prod-vms"
    assert pin["affine_host_group_name"] == "prod-hosts"


def test_get_or_none(cluster_factory, opts):
    cluster_factory["cluster"] = _fake_cluster(
        rules=[_make_rule("vm-affinity", "keep", key=1, vm_moids=["vm-1"])]
    )
    assert vim_drs_rule.get_or_none(opts, "domain-c9", "keep")["name"] == "keep"
    assert vim_drs_rule.get_or_none(opts, "domain-c9", "nope") is None


def test_create_vm_affinity_passes_spec(cluster_factory, opts, monkeypatch):
    monkeypatch.setattr(vim_drs_rule, "_vm_ref", lambda o, m, profile=None: _moref(m))
    vim_drs_rule.create_vm_affinity(opts, "domain-c9", "keep", ["vm-1", "vm-2"])
    cl = cluster_factory["cluster"]
    cl.ReconfigureComputeResource_Task.assert_called_once()
    spec = cl.ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    assert len(spec.rulesSpec) == 1
    assert spec.rulesSpec[0].operation == "add"
    assert spec.rulesSpec[0].info.name == "keep"
    assert isinstance(spec.rulesSpec[0].info, vim.cluster.AffinityRuleSpec)


def test_create_vm_anti_affinity_passes_spec(cluster_factory, opts, monkeypatch):
    monkeypatch.setattr(vim_drs_rule, "_vm_ref", lambda o, m, profile=None: _moref(m))
    vim_drs_rule.create_vm_anti_affinity(opts, "domain-c9", "split", ["vm-1", "vm-2"])
    spec = cluster_factory["cluster"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    assert isinstance(spec.rulesSpec[0].info, vim.cluster.AntiAffinityRuleSpec)


def test_create_vm_host_affine(cluster_factory, opts):
    vim_drs_rule.create_vm_host(opts, "domain-c9", "pin", "prod-vms", "prod-hosts", affine=True)
    spec = cluster_factory["cluster"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    rule = spec.rulesSpec[0].info
    assert isinstance(rule, vim.cluster.VmHostRuleInfo)
    assert rule.vmGroupName == "prod-vms"
    assert rule.affineHostGroupName == "prod-hosts"


def test_create_vm_host_anti_affine(cluster_factory, opts):
    vim_drs_rule.create_vm_host(opts, "domain-c9", "avoid", "test-vms", "prod-hosts", affine=False)
    spec = cluster_factory["cluster"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    rule = spec.rulesSpec[0].info
    assert rule.antiAffineHostGroupName == "prod-hosts"


def test_update_toggles_enabled(cluster_factory, opts, monkeypatch):
    monkeypatch.setattr(vim_drs_rule, "_vm_ref", lambda o, m, profile=None: _moref(m))
    cluster_factory["cluster"] = _fake_cluster(
        rules=[_make_rule("vm-affinity", "keep", key=7, enabled=True, vm_moids=["vm-1"])]
    )
    vim_drs_rule.update(opts, "domain-c9", "keep", enabled=False)
    spec = cluster_factory["cluster"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    assert spec.rulesSpec[0].operation == "edit"
    assert spec.rulesSpec[0].removeKey == 7
    assert spec.rulesSpec[0].info.enabled is False


def test_update_replaces_vm_moids(cluster_factory, opts, monkeypatch):
    monkeypatch.setattr(vim_drs_rule, "_vm_ref", lambda o, m, profile=None: _moref(m))
    cluster_factory["cluster"] = _fake_cluster(
        rules=[_make_rule("vm-affinity", "keep", key=7, vm_moids=["vm-1"])]
    )
    vim_drs_rule.update(opts, "domain-c9", "keep", vm_moids=["vm-9", "vm-10"])
    spec = cluster_factory["cluster"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    moids = [v._moId for v in spec.rulesSpec[0].info.vm]
    assert moids == ["vm-9", "vm-10"]


def test_delete_uses_remove_key(cluster_factory, opts):
    cluster_factory["cluster"] = _fake_cluster(
        rules=[_make_rule("vm-affinity", "keep", key=11, vm_moids=["vm-1"])]
    )
    vim_drs_rule.delete(opts, "domain-c9", "keep")
    spec = cluster_factory["cluster"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    assert spec.rulesSpec[0].operation == "remove"
    assert spec.rulesSpec[0].removeKey == 11


def test_delete_missing_raises(cluster_factory, opts):
    cluster_factory["cluster"] = _fake_cluster(rules=[])
    with pytest.raises(LookupError):
        vim_drs_rule.delete(opts, "domain-c9", "nope")


# Groups


def _vm_group(name, vm_moids):
    g = vim.cluster.VmGroup()
    g.name = name
    g.vm = [_moref(m) for m in vm_moids]
    return g


def _host_group(name, host_moids):
    g = vim.cluster.HostGroup()
    g.name = name
    g.host = [_host_moref(m) for m in host_moids]
    return g


def test_list_groups(cluster_factory, opts):
    cluster_factory["cluster"] = _fake_cluster(
        groups=[_vm_group("prod-vms", ["vm-1"]), _host_group("prod-hosts", ["host-1"])]
    )
    result = vim_drs_rule.list_groups(opts, "domain-c9")
    by_name = {g["name"]: g for g in result}
    assert by_name["prod-vms"]["kind"] == "vm"
    assert by_name["prod-vms"]["members"] == ["vm-1"]
    assert by_name["prod-hosts"]["kind"] == "host"


def test_create_vm_group(cluster_factory, opts, monkeypatch):
    monkeypatch.setattr(vim_drs_rule, "_vm_ref", lambda o, m, profile=None: _moref(m))
    vim_drs_rule.create_vm_group(opts, "domain-c9", "prod-vms", ["vm-1", "vm-2"])
    spec = cluster_factory["cluster"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    assert spec.groupSpec[0].operation == "add"
    assert isinstance(spec.groupSpec[0].info, vim.cluster.VmGroup)
    assert spec.groupSpec[0].info.name == "prod-vms"


def test_delete_group(cluster_factory, opts):
    vim_drs_rule.delete_group(opts, "domain-c9", "prod-vms")
    spec = cluster_factory["cluster"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    assert spec.groupSpec[0].operation == "remove"
    assert spec.groupSpec[0].removeKey == "prod-vms"


def test_get_group_returns_vm_group(cluster_factory, opts):
    cluster_factory["cluster"] = _fake_cluster(groups=[_vm_group("prod-vms", ["vm-1"])])
    g = vim_drs_rule.get_group(opts, "domain-c9", "prod-vms")
    assert g["kind"] == "vm"
    assert g["members"] == ["vm-1"]


def test_get_group_or_none_missing(cluster_factory, opts):
    cluster_factory["cluster"] = _fake_cluster(groups=[])
    assert vim_drs_rule.get_group_or_none(opts, "domain-c9", "missing") is None


def test_create_host_group(cluster_factory, opts, monkeypatch):
    monkeypatch.setattr(vim_drs_rule, "_host_ref", lambda o, m, profile=None: _host_moref(m))
    vim_drs_rule.create_host_group(opts, "domain-c9", "prod-hosts", ["host-1", "host-2"])
    spec = cluster_factory["cluster"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    assert spec.groupSpec[0].operation == "add"
    assert isinstance(spec.groupSpec[0].info, vim.cluster.HostGroup)


def test_update_group_replaces_vm_members(cluster_factory, opts, monkeypatch):
    monkeypatch.setattr(vim_drs_rule, "_vm_ref", lambda o, m, profile=None: _moref(m))
    cluster_factory["cluster"] = _fake_cluster(groups=[_vm_group("prod-vms", ["vm-1"])])
    cluster_factory["cluster"].ReconfigureComputeResource_Task.return_value = MagicMock(
        _moId="task-9"
    )
    out = vim_drs_rule.update_group(opts, "domain-c9", "prod-vms", vm_moids=["vm-7"])
    assert out == "task-9"
    spec = cluster_factory["cluster"].ReconfigureComputeResource_Task.call_args.kwargs["spec"]
    assert spec.groupSpec[0].operation == "edit"
    assert isinstance(spec.groupSpec[0].info, vim.cluster.VmGroup)
    assert spec.groupSpec[0].info.vm[0]._moId == "vm-7"  # noqa: SLF001


def test_update_group_missing_raises(cluster_factory, opts):
    cluster_factory["cluster"] = _fake_cluster(groups=[])
    with pytest.raises(LookupError):
        vim_drs_rule.update_group(opts, "domain-c9", "nope", vm_moids=["vm-1"])
