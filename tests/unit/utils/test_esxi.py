"""Tests for saltext.vcf.utils.esxi (direct/standalone mode, pyVmomi SOAP)."""

from unittest.mock import MagicMock
from unittest.mock import patch

from saltext.vcf.utils import esxi


def test_get_config_default(opts):
    cfg = esxi.get_config(opts)
    assert cfg == {
        "host": "esxi.test",
        "username": "root",
        "password": "p",
        "verify_ssl": False,
    }


def test_get_service_instance_connects_once(opts):
    si = MagicMock()
    with patch("saltext.vcf.utils.esxi.SmartConnect", return_value=si) as smart:
        first = esxi.get_service_instance(opts)
        second = esxi.get_service_instance(opts)
    assert first is si
    assert second is si
    # Second call should be served from the cache; SmartConnect not re-invoked.
    smart.assert_called_once()


def test_invalidate_service_instance_disconnects_and_drops_cache(opts):
    si = MagicMock()
    with patch("saltext.vcf.utils.esxi.SmartConnect", return_value=si):
        esxi.get_service_instance(opts)
    with patch("saltext.vcf.utils.esxi.Disconnect") as dc:
        esxi.invalidate_service_instance(opts)
    dc.assert_called_once_with(si)
    # Subsequent get_service_instance should reconnect rather than return the old si.
    new_si = MagicMock()
    with patch("saltext.vcf.utils.esxi.SmartConnect", return_value=new_si) as smart:
        assert esxi.get_service_instance(opts) is new_si
    smart.assert_called_once()


def test_get_service_instance_honors_host_port_suffix(opts):
    opts["pillar"]["saltext.vcf"]["esxi"]["host"] = "esxi.test:25443"
    si = MagicMock()
    with patch("saltext.vcf.utils.esxi.SmartConnect", return_value=si) as smart:
        esxi.get_service_instance(opts)
    kwargs = smart.call_args.kwargs
    assert kwargs["host"] == "esxi.test"
    assert kwargs["port"] == 25443


def test_get_host_system_returns_standalone_host(opts):
    host = MagicMock(name="HostSystem")
    si = MagicMock()
    # get_host_system uses a ContainerView (not fragile childEntity[0].host[0])
    # so mock that traversal.
    container = MagicMock()
    container.view = [host]
    content = si.RetrieveContent.return_value
    content.viewManager.CreateContainerView.return_value = container
    with patch("saltext.vcf.utils.esxi.SmartConnect", return_value=si):
        result = esxi.get_host_system(opts)
    assert result is host
    container.Destroy.assert_called_once()


def test_get_host_system_raises_when_no_hosts(opts):
    si = MagicMock()
    container = MagicMock()
    container.view = []
    content = si.RetrieveContent.return_value
    content.viewManager.CreateContainerView.return_value = container
    with patch("saltext.vcf.utils.esxi.SmartConnect", return_value=si):
        try:
            esxi.get_host_system(opts)
        except LookupError as exc:
            assert "no HostSystem" in str(exc)
        else:
            raise AssertionError("expected LookupError")
