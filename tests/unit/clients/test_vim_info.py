"""Tests for clients.vim_info (ServiceInstance.about)."""

from unittest.mock import MagicMock
from unittest.mock import patch

from saltext.vcf.clients import vim_info


def _fake_si(api_type="VirtualCenter"):
    si = MagicMock()
    content = MagicMock()
    about = MagicMock()
    about.name = "VMware vCenter Server"
    about.fullName = "VMware vCenter Server 9.0.0"
    about.apiType = api_type
    about.apiVersion = "9.0.0.0"
    about.productLineId = "vpx"
    about.version = "9.0.0"
    about.build = "24000000"
    about.osType = "linux-x64"
    about.instanceUuid = "instance-uuid-1"
    del about._wsdlName  # keep dir() clean of mock internals? not needed
    content.about = about
    si.RetrieveContent.return_value = content
    return si


def test_about_returns_plain_dict(opts):
    si = _fake_si()
    with patch("saltext.vcf.utils.vim.get_service_instance", return_value=si):
        out = vim_info.about(opts)
    assert out["apiType"] == "VirtualCenter"
    assert out["instanceUuid"] == "instance-uuid-1"
    # callables must be filtered out
    assert all(not callable(v) for k, v in out.items() if k in ("name", "apiVersion"))
