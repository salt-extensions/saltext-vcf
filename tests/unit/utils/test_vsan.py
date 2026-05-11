"""Tests for utils.vsan — vSAN SOAP stub setup."""

from unittest.mock import MagicMock
from unittest.mock import patch

from saltext.vmware.utils import vsan


def test_get_stub_caches(opts):
    fake_si = MagicMock()
    fake_si._stub.cookie = "cookie-1"  # noqa: SLF001
    with patch(
        "saltext.vmware.utils.vsan.vim_utils.get_service_instance",
        return_value=fake_si,
    ):
        with patch("saltext.vmware.utils.vsan.SoapStubAdapter") as adapter:
            adapter.return_value = MagicMock()
            stub1 = vsan.get_stub(opts)
            stub2 = vsan.get_stub(opts)
    assert stub1 is stub2
    assert adapter.call_count == 1


def test_get_stub_reuses_session_cookie(opts):
    fake_si = MagicMock()
    fake_si._stub.cookie = "session-cookie-X"  # noqa: SLF001
    with patch(
        "saltext.vmware.utils.vsan.vim_utils.get_service_instance",
        return_value=fake_si,
    ):
        with patch(
            "saltext.vmware.utils.vsan.SoapStubAdapter"
        ) as Adapter:  # pylint: disable=invalid-name
            stub_instance = MagicMock()
            Adapter.return_value = stub_instance
            vsan.get_stub(opts)
    assert stub_instance.cookie == "session-cookie-X"
    Adapter.assert_called_once()
    kwargs = Adapter.call_args.kwargs
    assert kwargs["path"] == "/vsanHealth"


def test_invalidate_clears_cache(opts):
    fake_si = MagicMock()
    fake_si._stub.cookie = "c"  # noqa: SLF001
    with patch(
        "saltext.vmware.utils.vsan.vim_utils.get_service_instance",
        return_value=fake_si,
    ):
        with patch("saltext.vmware.utils.vsan.SoapStubAdapter"):
            vsan.get_stub(opts)
            assert vsan._VSAN_STUB_CACHE
            vsan.invalidate_stub(opts)
            assert not vsan._VSAN_STUB_CACHE


def test_managed_object_accessors_use_stub(opts):
    fake_si = MagicMock()
    fake_si._stub.cookie = "c"  # noqa: SLF001
    with patch(
        "saltext.vmware.utils.vsan.vim_utils.get_service_instance",
        return_value=fake_si,
    ):
        with patch(
            "saltext.vmware.utils.vsan.SoapStubAdapter"
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
