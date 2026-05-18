"""Tests for clients.vim_vm (clone/create/reconfigure via SOAP)."""

from unittest.mock import MagicMock

import pytest
from pyVmomi import vim

from saltext.vcf.clients import vim_vm


def _fake_vm(name="src-vm", moid="vm-100", power_state="poweredOff", extra_config=None):
    vm = MagicMock()
    vm._moId = moid
    vm.name = name
    vm.runtime.powerState = power_state
    vm.config.extraConfig = [MagicMock(key=k, value=v) for k, v in (extra_config or {}).items()]
    vm.CloneVM_Task.return_value = MagicMock(_moId="task-clone-1")
    vm.ReconfigVM_Task.return_value = MagicMock(_moId="task-reconfig-1")
    vm.PowerOffVM_Task.return_value = MagicMock(_moId="task-off-1")
    vm.Destroy_Task.return_value = MagicMock(_moId="task-destroy-1")
    return vm


def _fake_folder():
    f = MagicMock()
    f.CreateVM_Task.return_value = MagicMock(_moId="task-create-1")
    return f


class _NamedDatastore(vim.Datastore):
    """Real pyVmomi Datastore ref with a ``.name`` shim that works without a stub."""

    _names: dict = {}

    @property  # type: ignore[override]
    def name(self):  # noqa: A003
        return _NamedDatastore._names.get(id(self), "ds")


def _fake_datastore(moid="ds-1", display="ds-1"):
    ds = vim.Datastore(moid, None)
    ds.__class__ = _NamedDatastore
    _NamedDatastore._names[id(ds)] = display
    return ds


def _fake_cluster(name="cl-1"):
    cl = MagicMock()
    cl.name = name
    cl.resourcePool = vim.ResourcePool(f"pool-{name}", None)
    return cl


@pytest.fixture
def lookup_factory(monkeypatch):
    state = {"vm": _fake_vm(), "type_to_obj": {}}

    def _vm(opts, vm_id, profile=None):
        return state["vm"]

    def _find_by_type(opts, vim_type, name_or_id, profile=None):
        key = (vim_type, name_or_id)
        if key in state["type_to_obj"]:
            return state["type_to_obj"][key]
        # Fall back to typed default
        if vim_type is vim.Folder:
            return _fake_folder()
        if vim_type is vim.Datastore:
            return _fake_datastore(name_or_id)
        if vim_type is vim.ClusterComputeResource:
            return _fake_cluster(name_or_id)
        if vim_type is vim.HostSystem:
            return MagicMock(parent=MagicMock(resourcePool=MagicMock()))
        return MagicMock()

    monkeypatch.setattr(vim_vm, "_vm", _vm)
    monkeypatch.setattr(vim_vm, "_find_by_type", _find_by_type)
    return state


# ---------- clone ----------


def test_clone_minimal_spec(lookup_factory, opts):
    vim_vm.clone(opts, "tmpl-1", "web-01", folder="group-v3", datastore="ds-1")
    call = lookup_factory["vm"].CloneVM_Task.call_args
    assert call.kwargs["name"] == "web-01"
    spec = call.kwargs["spec"]
    assert spec.powerOn is False
    assert spec.template is False
    assert spec.location.datastore._moId == "ds-1"  # noqa: SLF001
    # No config block when no hardware overrides
    assert spec.config is None


def test_clone_with_hardware_overrides(lookup_factory, opts):
    vim_vm.clone(
        opts,
        "tmpl-1",
        "web-01",
        folder="group-v3",
        datastore="ds-1",
        cpu_count=4,
        memory_mb=8192,
        annotation="cloned for prod",
    )
    spec = lookup_factory["vm"].CloneVM_Task.call_args.kwargs["spec"]
    assert spec.config.numCPUs == 4
    assert spec.config.memoryMB == 8192
    assert spec.config.annotation == "cloned for prod"


def test_clone_with_cluster_picks_root_pool(lookup_factory, opts):
    cluster = _fake_cluster()
    lookup_factory["type_to_obj"][(vim.ClusterComputeResource, "domain-c9")] = cluster
    vim_vm.clone(
        opts,
        "tmpl-1",
        "web-01",
        folder="group-v3",
        datastore="ds-1",
        cluster="domain-c9",
    )
    spec = lookup_factory["vm"].CloneVM_Task.call_args.kwargs["spec"]
    assert spec.location.pool is cluster.resourcePool


def test_clone_with_power_on_template_flag(lookup_factory, opts):
    vim_vm.clone(
        opts,
        "tmpl-1",
        "web-01",
        folder="group-v3",
        datastore="ds-1",
        power_on=True,
        template=True,
    )
    spec = lookup_factory["vm"].CloneVM_Task.call_args.kwargs["spec"]
    assert spec.powerOn is True
    assert spec.template is True


def test_clone_with_customization_spec(lookup_factory, opts):
    cust = vim.vm.customization.Specification()
    vim_vm.clone(
        opts,
        "tmpl-1",
        "web-01",
        folder="group-v3",
        datastore="ds-1",
        customization=cust,
    )
    spec = lookup_factory["vm"].CloneVM_Task.call_args.kwargs["spec"]
    assert spec.customization is cust


# ---------- create ----------


def test_create_requires_placement(lookup_factory, opts):
    with pytest.raises(ValueError, match="cluster, host, or resource_pool"):
        vim_vm.create(opts, "vm-1", folder="group-v3", datastore="ds-1")


def test_create_with_cluster_uses_root_pool(lookup_factory, opts):
    cluster = _fake_cluster()
    lookup_factory["type_to_obj"][(vim.ClusterComputeResource, "domain-c9")] = cluster

    folder = _fake_folder()
    lookup_factory["type_to_obj"][(vim.Folder, "group-v3")] = folder

    vim_vm.create(
        opts,
        "vm-1",
        folder="group-v3",
        datastore="ds-1",
        cluster="domain-c9",
        cpu_count=2,
        memory_mb=4096,
    )
    call = folder.CreateVM_Task.call_args
    assert call.kwargs["config"].numCPUs == 2
    assert call.kwargs["config"].memoryMB == 4096
    assert call.kwargs["pool"] is cluster.resourcePool


# ---------- reconfigure ----------


def test_reconfigure_only_passes_non_none(lookup_factory, opts):
    vim_vm.reconfigure(opts, "vm-100", cpu_count=4)
    spec = lookup_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"]
    assert spec.numCPUs == 4
    assert spec.memoryMB is None
    assert spec.annotation is None


def test_reconfigure_advanced_settings_emit_extraconfig(lookup_factory, opts):
    vim_vm.reconfigure(
        opts,
        "vm-100",
        advanced_settings={"isolation.tools.copy.disable": "true"},
    )
    spec = lookup_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"]
    assert len(spec.extraConfig) == 1
    assert spec.extraConfig[0].key == "isolation.tools.copy.disable"
    assert spec.extraConfig[0].value == "true"


def test_reconfigure_cores_per_socket(lookup_factory, opts):
    vim_vm.reconfigure(opts, "vm-100", cpu_count=8, cores_per_socket=4)
    spec = lookup_factory["vm"].ReconfigVM_Task.call_args.kwargs["spec"]
    assert spec.numCPUs == 8
    assert spec.numCoresPerSocket == 4


def test_get_advanced_settings(lookup_factory, opts):
    lookup_factory["vm"] = _fake_vm(extra_config={"a": "1", "b": "2"})
    result = vim_vm.get_advanced_settings(opts, "vm-100")
    assert result == {"a": "1", "b": "2"}


# ---------- destroy / mark ----------


def test_destroy_powers_off_first(lookup_factory, opts):
    lookup_factory["vm"] = _fake_vm(power_state="poweredOn")
    vim_vm.destroy(opts, "vm-100")
    lookup_factory["vm"].PowerOffVM_Task.assert_called_once()
    lookup_factory["vm"].Destroy_Task.assert_called_once()


def test_destroy_skips_poweroff_when_already_off(lookup_factory, opts):
    lookup_factory["vm"] = _fake_vm(power_state="poweredOff")
    vim_vm.destroy(opts, "vm-100")
    lookup_factory["vm"].PowerOffVM_Task.assert_not_called()
    lookup_factory["vm"].Destroy_Task.assert_called_once()


def test_mark_as_template(lookup_factory, opts):
    vim_vm.mark_as_template(opts, "vm-100")
    lookup_factory["vm"].MarkAsTemplate.assert_called_once()


def test_mark_as_virtual_machine(lookup_factory, opts):
    pool = MagicMock()
    lookup_factory["type_to_obj"][(vim.ResourcePool, "resgroup-c9")] = pool
    vim_vm.mark_as_virtual_machine(opts, "tmpl-1", "resgroup-c9")
    lookup_factory["vm"].MarkAsVirtualMachine.assert_called_once_with(pool=pool, host=None)
