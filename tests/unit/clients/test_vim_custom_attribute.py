"""Tests for clients.vim_custom_attribute (SOAP)."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from saltext.vcf.clients import vim_custom_attribute


def _make_field(key, name, mo_type=None):
    f = MagicMock()
    f.key = key
    # MagicMock's `.name` attribute is reserved — set via configure_mock
    f.configure_mock(name=name)
    f.managedObjectType = type(mo_type, (), {"__name__": mo_type}) if mo_type else None
    return f


def test_list_returns_dicts(opts):
    cfm = MagicMock()
    cfm.field = [_make_field(1, "owner", "VirtualMachine"), _make_field(2, "team")]
    with patch(
        "saltext.vcf.clients.vim_custom_attribute.soap.custom_fields_manager",
        return_value=cfm,
    ):
        result = vim_custom_attribute.list_(opts)
    assert result[0]["name"] == "owner"
    assert result[0]["managed_object_type"] == "VirtualMachine"
    assert result[1]["managed_object_type"] is None


def test_get_finds_by_name(opts):
    cfm = MagicMock()
    cfm.field = [_make_field(1, "owner")]
    with patch(
        "saltext.vcf.clients.vim_custom_attribute.soap.custom_fields_manager",
        return_value=cfm,
    ):
        assert vim_custom_attribute.get(opts, "owner")["key"] == 1
        assert vim_custom_attribute.get(opts, "missing") is None


def test_add_creates_field(opts):
    cfm = MagicMock()
    # MagicMock's `.name` is reserved — set it via configure_mock
    new_field = MagicMock(key=42)
    new_field.configure_mock(name="owner")
    cfm.AddCustomFieldDef.return_value = new_field
    with patch(
        "saltext.vcf.clients.vim_custom_attribute.soap.custom_fields_manager",
        return_value=cfm,
    ):
        result = vim_custom_attribute.add(opts, "owner", managed_object_type="VirtualMachine")
    assert result == {"key": 42, "name": "owner"}
    cfm.AddCustomFieldDef.assert_called_once()


def test_remove_by_name(opts):
    cfm = MagicMock()
    cfm.field = [_make_field(7, "owner")]
    with patch(
        "saltext.vcf.clients.vim_custom_attribute.soap.custom_fields_manager",
        return_value=cfm,
    ):
        vim_custom_attribute.remove(opts, "owner")
    cfm.RemoveCustomFieldDef.assert_called_once_with(key=7)


def test_remove_missing_raises(opts):
    cfm = MagicMock()
    cfm.field = []
    with patch(
        "saltext.vcf.clients.vim_custom_attribute.soap.custom_fields_manager",
        return_value=cfm,
    ):
        with pytest.raises(LookupError):
            vim_custom_attribute.remove(opts, "missing")
