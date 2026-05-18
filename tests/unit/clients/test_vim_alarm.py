"""Tests for clients.vim_alarm."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from pyVmomi import vim as pyvim

from saltext.vcf.clients import vim_alarm


@pytest.fixture
def fake_alarm():
    a = MagicMock()
    a._moId = "alarm-1"
    a.info.name = "Test Alarm"
    a.info.description = "desc"
    a.info.enabled = True
    a.info.systemName = ""
    a.info.entity._moId = "folder-1"
    return a


def test_list_returns_dicts(opts, fake_alarm):
    am = MagicMock()
    am.GetAlarm.return_value = [fake_alarm]
    with patch("saltext.vcf.clients.vim_alarm.soap.alarm_manager", return_value=am):
        with patch("saltext.vcf.clients.vim_alarm.soap.root_folder", return_value=object()):
            result = vim_alarm.list_(opts)
    assert result == [
        {
            "key": "alarm-1",
            "name": "Test Alarm",
            "description": "desc",
            "enabled": True,
            "system_name": "",
            "entity_id": "folder-1",
        }
    ]


def test_get_finds_by_name(opts, fake_alarm):
    am = MagicMock()
    am.GetAlarm.return_value = [fake_alarm]
    with patch("saltext.vcf.clients.vim_alarm.soap.alarm_manager", return_value=am):
        with patch("saltext.vcf.clients.vim_alarm.soap.root_folder", return_value=object()):
            assert vim_alarm.get(opts, "Test Alarm")["key"] == "alarm-1"
            assert vim_alarm.get(opts, "Nope") is None


def test_create_calls_create_alarm(opts):
    am = MagicMock()
    am.CreateAlarm.return_value = MagicMock(_moId="alarm-99")
    # Use a real EventAlarmExpression — pyVmomi type-checks AlarmSpec.expression
    expression = pyvim.alarm.EventAlarmExpression()
    with patch("saltext.vcf.clients.vim_alarm.soap.alarm_manager", return_value=am):
        with patch("saltext.vcf.clients.vim_alarm.soap.root_folder", return_value="root"):
            mo_id = vim_alarm.create(opts, "name", "desc", expression=expression)
    assert mo_id == "alarm-99"
    am.CreateAlarm.assert_called_once()


def test_delete_calls_remove(opts):
    si = MagicMock()
    with patch("saltext.vcf.clients.vim_alarm.soap.get_service_instance", return_value=si):
        with patch(
            "saltext.vcf.clients.vim_alarm.vim.alarm.Alarm"
        ) as Alarm:  # pylint: disable=invalid-name
            mo = MagicMock()
            Alarm.return_value = mo
            vim_alarm.delete(opts, "alarm-1")
            mo.RemoveAlarm.assert_called_once()
