"""Tests for saltext.vcf.utils.vim (pyVmomi SOAP wrapper).

pyVmomi network calls are mocked at the SmartConnect boundary.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from saltext.vcf.utils import vim as soap


@pytest.fixture
def mock_si():
    """Return a fake ServiceInstance with realistic .RetrieveContent()."""
    si = MagicMock()
    content = MagicMock()
    si.RetrieveContent.return_value = content
    return si


def test_get_service_instance_caches(opts, mock_si):
    with patch("saltext.vcf.utils.vim.SmartConnect", return_value=mock_si) as connect:
        si1 = soap.get_service_instance(opts)
        si2 = soap.get_service_instance(opts)
    assert si1 is si2
    assert connect.call_count == 1


def test_get_service_instance_passes_opts(opts, mock_si):
    with patch("saltext.vcf.utils.vim.SmartConnect", return_value=mock_si) as connect:
        soap.get_service_instance(opts)
    kwargs = connect.call_args.kwargs
    assert kwargs["host"] == "vc.test"
    assert kwargs["user"] == "u"
    assert kwargs["pwd"] == "p"


def test_invalidate_calls_disconnect(opts, mock_si):
    with patch("saltext.vcf.utils.vim.SmartConnect", return_value=mock_si):
        soap.get_service_instance(opts)
    with patch("saltext.vcf.utils.vim.Disconnect") as dc:
        soap.invalidate_service_instance(opts)
    dc.assert_called_once_with(mock_si)
    assert not soap._SI_CACHE


def test_manager_accessors(opts, mock_si):
    with patch("saltext.vcf.utils.vim.SmartConnect", return_value=mock_si):
        assert soap.alarm_manager(opts) is mock_si.RetrieveContent.return_value.alarmManager
        assert soap.perf_manager(opts) is mock_si.RetrieveContent.return_value.perfManager
        assert soap.extension_manager(opts) is mock_si.RetrieveContent.return_value.extensionManager
        assert soap.license_manager(opts) is mock_si.RetrieveContent.return_value.licenseManager


# ---------------------------------------------------------------------------
# Standalone-ESXi routing
# ---------------------------------------------------------------------------


def test_is_standalone_esxi_true_when_only_esxi_configured(opts_standalone):
    assert soap.is_standalone_esxi(opts_standalone) is True


def test_is_standalone_esxi_false_when_vcenter_configured(opts):
    assert soap.is_standalone_esxi(opts) is False


def test_get_service_instance_delegates_to_esxi_for_standalone(opts_standalone):
    """When ``saltext.vcf.vcenter`` is unset, get_service_instance forwards
    to ``saltext.vcf.utils.esxi.get_service_instance`` (which reads the
    ``saltext.vcf.esxi`` pillar and calls SmartConnect against the ESXi
    host directly).
    """
    fake_si = MagicMock(name="ESXi SI")
    with patch(
        "saltext.vcf.utils.esxi.get_service_instance",
        return_value=fake_si,
    ) as delegate:
        result = soap.get_service_instance(opts_standalone)
    assert result is fake_si
    delegate.assert_called_once()


def test_resolve_host_system_matches_by_name(opts, mock_si):
    host = MagicMock()
    host._moId = "host-42"
    host.name = "esxi-01"
    container = MagicMock()
    container.view = [host]
    content = mock_si.RetrieveContent.return_value
    content.viewManager.CreateContainerView.return_value = container
    with patch("saltext.vcf.utils.vim.SmartConnect", return_value=mock_si):
        result = soap.resolve_host_system(opts, "esxi-01")
    assert result is host
    container.Destroy.assert_called_once()


def test_resolve_host_system_matches_by_vmkernel_ip(opts, mock_si):
    """Callers that only know the mgmt IP can still resolve the host."""
    vnic = MagicMock()
    vnic.spec.ip.ipAddress = "10.0.0.5"
    host = MagicMock()
    host._moId = "host-42"
    host.name = "sysrescue"  # stale DHCP hostname — deliberate red herring
    host.config.network.vnic = [vnic]
    container = MagicMock()
    container.view = [host]
    content = mock_si.RetrieveContent.return_value
    content.viewManager.CreateContainerView.return_value = container
    with patch("saltext.vcf.utils.vim.SmartConnect", return_value=mock_si):
        result = soap.resolve_host_system(opts, "10.0.0.5")
    assert result is host


def test_resolve_host_system_standalone_single_host_fallback(opts_standalone):
    """Standalone: sole host in tree returned even if name_or_id doesn't match."""
    host = MagicMock()
    host._moId = "ha-host"
    host.name = "sysrescue"
    host.config.network.vnic = []
    container = MagicMock()
    container.view = [host]
    fake_si = MagicMock()
    content = fake_si.RetrieveContent.return_value
    content.viewManager.CreateContainerView.return_value = container
    with patch(
        "saltext.vcf.utils.esxi.get_service_instance",
        return_value=fake_si,
    ):
        result = soap.resolve_host_system(opts_standalone, "192.168.0.24")
    assert result is host


def test_resolve_host_system_raises_when_no_match(opts, mock_si):
    container = MagicMock()
    container.view = []
    content = mock_si.RetrieveContent.return_value
    content.viewManager.CreateContainerView.return_value = container
    with patch("saltext.vcf.utils.vim.SmartConnect", return_value=mock_si):
        try:
            soap.resolve_host_system(opts, "nope")
        except LookupError as exc:
            assert "nope" in str(exc)
        else:
            raise AssertionError("expected LookupError")
