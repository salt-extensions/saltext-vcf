"""Tests for clients.vim_scheduled_task (SOAP)."""

from datetime import datetime
from datetime import timezone
from unittest.mock import MagicMock

import pytest

from saltext.vmware.clients import vim_scheduled_task


def _make_task(mo_id, name, enabled=True):
    t = MagicMock()
    t._moId = mo_id  # noqa: SLF001
    t.info.name = name
    t.info.description = "desc"
    t.info.enabled = enabled
    t.info.entity = MagicMock(_moId="host-1")
    t.info.scheduler = MagicMock()
    type(t.info.scheduler).__name__ = "OnceTaskScheduler"
    t.info.lastModifiedUser = "admin@vsphere.local"
    t.info.nextRunTime = datetime(2026, 5, 12, 9, 0, tzinfo=timezone.utc)
    t.info.state = "ready"
    return t


@pytest.fixture
def stm_factory(monkeypatch):
    stm = MagicMock()
    monkeypatch.setattr(vim_scheduled_task, "_stm", lambda opts, profile=None: stm)
    return stm


def test_list_all_tasks(opts, stm_factory):
    stm_factory.scheduledTask = [_make_task("st-1", "task-A"), _make_task("st-2", "task-B")]
    out = vim_scheduled_task.list_(opts)
    assert len(out) == 2
    assert out[0]["name"] == "task-A"
    assert out[0]["next_run_time"].startswith("2026-05-12")


def test_get_by_name(opts, stm_factory):
    stm_factory.scheduledTask = [_make_task("st-1", "task-A")]
    out = vim_scheduled_task.get(opts, "task-A")
    assert out["name"] == "task-A"


def test_get_or_none_missing(opts, stm_factory):
    stm_factory.scheduledTask = []
    assert vim_scheduled_task.get_or_none(opts, "missing") is None


def test_delete_calls_remove(opts, stm_factory):
    task = _make_task("st-1", "task-A")
    stm_factory.scheduledTask = [task]
    assert vim_scheduled_task.delete(opts, "task-A") is True
    task.RemoveScheduledTask.assert_called_once()


def test_run_now_calls_run(opts, stm_factory):
    task = _make_task("st-1", "task-A")
    stm_factory.scheduledTask = [task]
    assert vim_scheduled_task.run_now(opts, "task-A") is True
    task.RunScheduledTask.assert_called_once()
