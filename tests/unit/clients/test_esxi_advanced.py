"""Tests for clients.esxi_advanced (ESXi HostSystem advancedOption via SOAP)."""

from unittest.mock import MagicMock
from unittest.mock import patch

from pyVmomi import vim

from saltext.vcf.clients import esxi_advanced


def _opt(key, value):
    return vim.option.OptionValue(key=key, value=value)


def _host_with_advanced_option(mgr):
    host = MagicMock()
    host.configManager.advancedOption = mgr
    return host


def test_set_value_mutates_existing_typed_object(opts):
    """Same fetch-mutate requirement as the vCenter-side fix: a freshly-built
    ``OptionValue`` from a bare Python value can serialize with the wrong
    XSD type and get rejected by the host with
    ``vmodl.fault.InvalidArgument(invalidProperty='value')`` for settings
    that aren't plain ``xsd:int``/``xsd:string``.
    """
    mgr = MagicMock()
    existing_opt = _opt("Some.Setting", 32)
    mgr.QueryOptions.return_value = [existing_opt]
    host = _host_with_advanced_option(mgr)

    with patch("saltext.vcf.clients.esxi_advanced.esxi.get_host_system", return_value=host):
        esxi_advanced.set_value(opts, "Some.Setting", 64)

    changed = mgr.UpdateValues.call_args.kwargs["changedValue"]
    assert changed[0] is existing_opt
    assert changed[0].value == 64


def test_set_value_never_set_before_falls_back_to_fresh_object(opts):
    mgr = MagicMock()
    mgr.QueryOptions.return_value = []
    host = _host_with_advanced_option(mgr)

    with patch("saltext.vcf.clients.esxi_advanced.esxi.get_host_system", return_value=host):
        esxi_advanced.set_value(opts, "Brand.New.Setting", 64)

    changed = mgr.UpdateValues.call_args.kwargs["changedValue"]
    assert changed[0].key == "Brand.New.Setting"
    assert changed[0].value == 64
