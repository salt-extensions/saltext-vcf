"""Tests for utils.vsan — vSAN SOAP stub setup."""

from unittest.mock import MagicMock
from unittest.mock import patch

from saltext.vcf.utils import vsan


def test_get_stub_caches(opts):
    fake_si = MagicMock()
    fake_si._stub.cookie = "cookie-1"  # noqa: SLF001
    with patch(
        "saltext.vcf.utils.vsan.vim_utils.get_service_instance",
        return_value=fake_si,
    ):
        with patch("saltext.vcf.utils.vsan.SoapStubAdapter") as adapter:
            adapter.return_value = MagicMock()
            stub1 = vsan.get_stub(opts)
            stub2 = vsan.get_stub(opts)
    assert stub1 is stub2
    assert adapter.call_count == 1


def test_get_stub_reuses_session_cookie(opts):
    fake_si = MagicMock()
    fake_si._stub.cookie = "session-cookie-X"  # noqa: SLF001
    with patch(
        "saltext.vcf.utils.vsan.vim_utils.get_service_instance",
        return_value=fake_si,
    ):
        with patch(
            "saltext.vcf.utils.vsan.SoapStubAdapter"
        ) as Adapter:  # pylint: disable=invalid-name
            stub_instance = MagicMock()
            Adapter.return_value = stub_instance
            vsan.get_stub(opts)
    assert stub_instance.cookie == "session-cookie-X"
    Adapter.assert_called_once()
    kwargs = Adapter.call_args.kwargs
    assert kwargs["path"] == "/vsanHealth"


def test_get_stub_routes_through_proxy_when_present(opts):
    """VCF 9.x appliances front every service behind a local envoy/system
    proxy -- the vim.py /sdk connection already routes through it via
    ``_proxy_for_host``. This stub is built independently of that
    connection, so it needs the exact same treatment or it gets
    ``ConnectionRefusedError`` even though the main vim connection works.
    """
    fake_si = MagicMock()
    fake_si._stub.cookie = "cookie-1"  # noqa: SLF001
    with (
        patch(
            "saltext.vcf.utils.vsan.vim_utils.get_service_instance",
            return_value=fake_si,
        ),
        patch(
            "saltext.vcf.utils.vsan.vim_utils._proxy_for_host",
            return_value=("127.0.0.1", 1234),
        ),
        patch("saltext.vcf.utils.vsan.SoapStubAdapter") as adapter,
    ):
        adapter.return_value = MagicMock()
        vsan.get_stub(opts)
    kwargs = adapter.call_args.kwargs
    assert kwargs["httpProxyHost"] == "127.0.0.1"
    assert kwargs["httpProxyPort"] == 1234


def test_invalidate_clears_cache(opts):
    fake_si = MagicMock()
    fake_si._stub.cookie = "c"  # noqa: SLF001
    with patch(
        "saltext.vcf.utils.vsan.vim_utils.get_service_instance",
        return_value=fake_si,
    ):
        with patch("saltext.vcf.utils.vsan.SoapStubAdapter"):
            vsan.get_stub(opts)
            assert vsan._VSAN_STUB_CACHE
            vsan.invalidate_stub(opts)
            assert not vsan._VSAN_STUB_CACHE


def test_managed_object_accessors_use_stub(opts):
    fake_si = MagicMock()
    fake_si._stub.cookie = "c"  # noqa: SLF001
    with patch(
        "saltext.vcf.utils.vsan.vim_utils.get_service_instance",
        return_value=fake_si,
    ):
        with patch(
            "saltext.vcf.utils.vsan.SoapStubAdapter"
        ) as Adapter:  # pylint: disable=invalid-name
            stub = MagicMock()
            Adapter.return_value = stub
            for fn in (
                vsan.cluster_config_system,
                vsan.cluster_health_system,
                vsan.disk_management_system,
                vsan.iscsi_target_system,
                vsan.stretched_cluster_system,
                vsan.object_system,
            ):
                # Each accessor should produce a managed-object on the stub
                mo = fn(opts)
                assert mo is not None
