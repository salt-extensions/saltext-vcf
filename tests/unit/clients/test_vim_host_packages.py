"""Tests for clients.vim_host_packages (VIB listing)."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from saltext.vcf.clients import vim_host_packages


def _pkg(name, version="1.0", vendor="VMware"):
    p = MagicMock()
    p.name = name
    p.version = version
    p.vendor = vendor
    p.summary = "summary"
    p.description = "desc"
    p.acceptanceLevel = "VMwareCertified"
    p.maintenanceModeRequired = False
    p.creationDate = None
    return p


def test_list_all(opts):
    h = MagicMock()
    h.name = "esxi-01"
    h.configManager.imageConfigManager.FetchSoftwarePackages.return_value = [
        _pkg("esx-base"), _pkg("vsan"),
    ]
    with patch.object(vim_host_packages, "_resolve", return_value=h):
        out = vim_host_packages.list_(opts, "esxi-01")
    assert set(out) == {"esx-base", "vsan"}
    assert out["esx-base"]["version"] == "1.0"


def test_list_filtered(opts):
    h = MagicMock()
    h.name = "esxi-01"
    h.configManager.imageConfigManager.FetchSoftwarePackages.return_value = [
        _pkg("esx-base"), _pkg("vsan"),
    ]
    with patch.object(vim_host_packages, "_resolve", return_value=h):
        out = vim_host_packages.list_(opts, "esxi-01", pkg_name="vsan")
    assert set(out) == {"vsan"}


def test_list_missing_manager_raises(opts):
    h = MagicMock()
    h.name = "esxi-01"
    h.configManager.imageConfigManager = None
    with patch.object(vim_host_packages, "_resolve", return_value=h):
        with pytest.raises(RuntimeError):
            vim_host_packages.list_(opts, "esxi-01")
