"""Tests for saltext.vmware.utils.vim (pyVmomi SOAP wrapper).

pyVmomi network calls are mocked at the SmartConnect boundary.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from saltext.vmware.utils import vim as soap


@pytest.fixture
def mock_si():
    """Return a fake ServiceInstance with realistic .RetrieveContent()."""
    si = MagicMock()
    content = MagicMock()
    si.RetrieveContent.return_value = content
    return si


def test_get_service_instance_caches(opts, mock_si):
    with patch("saltext.vmware.utils.vim.SmartConnect", return_value=mock_si) as connect:
        si1 = soap.get_service_instance(opts)
        si2 = soap.get_service_instance(opts)
    assert si1 is si2
    assert connect.call_count == 1


def test_get_service_instance_passes_opts(opts, mock_si):
    with patch("saltext.vmware.utils.vim.SmartConnect", return_value=mock_si) as connect:
        soap.get_service_instance(opts)
    kwargs = connect.call_args.kwargs
    assert kwargs["host"] == "vc.test"
    assert kwargs["user"] == "u"
    assert kwargs["pwd"] == "p"


def test_invalidate_calls_disconnect(opts, mock_si):
    with patch("saltext.vmware.utils.vim.SmartConnect", return_value=mock_si):
        soap.get_service_instance(opts)
    with patch("saltext.vmware.utils.vim.Disconnect") as dc:
        soap.invalidate_service_instance(opts)
    dc.assert_called_once_with(mock_si)
    assert not soap._SI_CACHE


def test_manager_accessors(opts, mock_si):
    with patch("saltext.vmware.utils.vim.SmartConnect", return_value=mock_si):
        assert soap.alarm_manager(opts) is mock_si.RetrieveContent.return_value.alarmManager
        assert soap.perf_manager(opts) is mock_si.RetrieveContent.return_value.perfManager
        assert soap.extension_manager(opts) is mock_si.RetrieveContent.return_value.extensionManager
        assert soap.license_manager(opts) is mock_si.RetrieveContent.return_value.licenseManager
