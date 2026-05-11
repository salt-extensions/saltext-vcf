"""Tests for clients.vim_vm_snapshot (SOAP-based)."""

from datetime import datetime
from datetime import timezone
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from saltext.vmware.clients import vim_vm_snapshot


def _make_snapshot_node(mo_id, name, children=None):
    node = MagicMock()
    node.snapshot._moId = mo_id  # noqa: SLF001
    node.name = name
    node.description = ""
    node.createTime = datetime(2026, 5, 10, tzinfo=timezone.utc)
    node.state = "poweredOn"
    node.quiesced = False
    node.childSnapshotList = children or []
    return node


def _make_vm_with_snapshots(snaps):
    vm = MagicMock()
    vm._moId = "vm-1"  # noqa: SLF001
    vm.name = "my-vm"
    vm.snapshot.rootSnapshotList = snaps
    return vm


def test_list_returns_tree(opts):
    child = _make_snapshot_node("snap-child", "after-patch")
    root = _make_snapshot_node("snap-root", "baseline", children=[child])
    vm = _make_vm_with_snapshots([root])
    with patch("saltext.vmware.clients.vim_vm_snapshot._find_vm", return_value=vm):
        result = vim_vm_snapshot.list_(opts, "vm-1")
    assert result[0]["name"] == "baseline"
    assert result[0]["children"][0]["name"] == "after-patch"


def test_list_returns_empty_when_no_snapshots(opts):
    vm = MagicMock()
    vm.snapshot = None
    with patch("saltext.vmware.clients.vim_vm_snapshot._find_vm", return_value=vm):
        assert vim_vm_snapshot.list_(opts, "vm-1") == []


def test_current_returns_dict(opts):
    root = _make_snapshot_node("snap-1", "baseline")
    vm = _make_vm_with_snapshots([root])
    vm.snapshot.currentSnapshot._moId = "snap-1"  # noqa: SLF001
    with patch("saltext.vmware.clients.vim_vm_snapshot._find_vm", return_value=vm):
        cur = vim_vm_snapshot.current(opts, "vm-1")
    assert cur == {"id": "snap-1", "name": "baseline"}


def test_create_returns_task_id(opts):
    vm = MagicMock()
    vm.CreateSnapshot_Task.return_value = MagicMock(_moId="task-1")
    with patch("saltext.vmware.clients.vim_vm_snapshot._find_vm", return_value=vm):
        task = vim_vm_snapshot.create(opts, "vm-1", "name", memory=True, quiesce=True)
    assert task == "task-1"
    kwargs = vm.CreateSnapshot_Task.call_args.kwargs
    assert kwargs["memory"] is True
    assert kwargs["quiesce"] is True


def test_revert_finds_by_name(opts):
    root = _make_snapshot_node("snap-1", "baseline")
    root.snapshot.RevertToSnapshot_Task.return_value = MagicMock(_moId="task-2")
    vm = _make_vm_with_snapshots([root])
    with patch("saltext.vmware.clients.vim_vm_snapshot._find_vm", return_value=vm):
        assert vim_vm_snapshot.revert(opts, "vm-1", "baseline") == "task-2"


def test_revert_raises_when_missing(opts):
    vm = _make_vm_with_snapshots([_make_snapshot_node("snap-1", "other")])
    with patch("saltext.vmware.clients.vim_vm_snapshot._find_vm", return_value=vm):
        with pytest.raises(LookupError):
            vim_vm_snapshot.revert(opts, "vm-1", "missing")


def test_remove_all(opts):
    vm = MagicMock()
    vm.RemoveAllSnapshots_Task.return_value = MagicMock(_moId="task-3")
    with patch("saltext.vmware.clients.vim_vm_snapshot._find_vm", return_value=vm):
        assert vim_vm_snapshot.remove_all(opts, "vm-1") == "task-3"
