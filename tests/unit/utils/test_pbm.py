"""Tests for utils.pbm — PBM SOAP stub setup."""

from unittest.mock import MagicMock
from unittest.mock import patch

from saltext.vcf.utils import pbm

# pyVmomi formats si._stub.cookie as: vmware_soap_session="<token>"; Path=/; ...
_RAW_COOKIE = 'vmware_soap_session="cookie-1"; Path=/; Secure; HttpOnly'


def _cookie(token):
    return f'vmware_soap_session="{token}"; Path=/; Secure; HttpOnly'


def test_get_stub_caches(opts):
    fake_si = MagicMock()
    fake_si._stub.cookie = _cookie("cookie-1")  # noqa: SLF001
    with patch(
        "saltext.vcf.utils.pbm.vim_utils.get_service_instance",
        return_value=fake_si,
    ), patch("saltext.vcf.utils.pbm.SoapStubAdapter") as adapter:
        adapter.return_value = MagicMock()
        stub1 = pbm.get_stub(opts)
        stub2 = pbm.get_stub(opts)
    assert stub1 is stub2
    assert adapter.call_count == 1


def test_get_stub_reuses_session_cookie(opts):
    fake_si = MagicMock()
    fake_si._stub.cookie = _cookie("session-cookie-X")  # noqa: SLF001
    with patch(
        "saltext.vcf.utils.pbm.vim_utils.get_service_instance",
        return_value=fake_si,
    ), patch("saltext.vcf.utils.pbm.SoapStubAdapter") as adapter:
        stub_instance = MagicMock()
        adapter.return_value = stub_instance
        pbm.get_stub(opts)
    assert stub_instance.cookie == _cookie("session-cookie-X")
    kwargs = adapter.call_args.kwargs
    assert kwargs["path"] == "/pbm/sdk"


def test_get_stub_sets_vc_session_cookie_request_context(opts):
    """PBM's ProfileManager validates sessions through the VMODL
    request-context ``vcSessionCookie`` field, not the plain HTTP Cookie
    header alone -- without this, every PBM call fails with
    ``vim.fault.NotAuthenticated`` even though the stub connects fine and
    the Cookie header is set correctly.
    """
    fake_si = MagicMock()
    fake_si._stub.cookie = _cookie("session-cookie-X")  # noqa: SLF001
    with patch(
        "saltext.vcf.utils.pbm.vim_utils.get_service_instance",
        return_value=fake_si,
    ), patch("saltext.vcf.utils.pbm.SoapStubAdapter") as adapter:
        adapter.return_value = MagicMock()
        pbm.get_stub(opts)
    assert pbm.VmomiSupport.GetRequestContext()["vcSessionCookie"] == "session-cookie-X"


def test_get_stub_routes_through_proxy_when_present(opts):
    """Same VCF 9.x local-envoy-proxy requirement as utils.vsan -- this stub
    is built independently of utils.vim's main /sdk connection, so it needs
    the exact same explicit httpProxyHost/httpProxyPort treatment.
    """
    fake_si = MagicMock()
    fake_si._stub.cookie = _RAW_COOKIE  # noqa: SLF001
    with patch(
        "saltext.vcf.utils.pbm.vim_utils.get_service_instance",
        return_value=fake_si,
    ), patch(
        "saltext.vcf.utils.pbm.vim_utils._proxy_for_host",
        return_value=("127.0.0.1", 1234),
    ), patch("saltext.vcf.utils.pbm.SoapStubAdapter") as adapter:
        adapter.return_value = MagicMock()
        pbm.get_stub(opts)
    kwargs = adapter.call_args.kwargs
    assert kwargs["httpProxyHost"] == "127.0.0.1"
    assert kwargs["httpProxyPort"] == 1234


def test_invalidate_clears_cache(opts):
    fake_si = MagicMock()
    fake_si._stub.cookie = _RAW_COOKIE  # noqa: SLF001
    with patch(
        "saltext.vcf.utils.pbm.vim_utils.get_service_instance",
        return_value=fake_si,
    ), patch("saltext.vcf.utils.pbm.SoapStubAdapter"):
        pbm.get_stub(opts)
        assert pbm._PBM_STUB_CACHE
        pbm.invalidate_stub(opts)
        assert not pbm._PBM_STUB_CACHE
