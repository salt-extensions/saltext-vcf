"""Tests for modules.vcf_esxi_ntp."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from saltext.vcf.modules import vcf_esxi_ntp as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def _service(key, running):
    svc = MagicMock()
    svc.key = key
    svc.running = running
    svc.policy = "on"
    svc.label = key
    return svc


def _fake_host(*, servers=("pool.ntp.org",), ntpd_running=True):
    host = MagicMock()
    dt_info = MagicMock()
    dt_info.ntpConfig.server = list(servers)
    # esxi_ntp.get reads the ``dateTimeInfo`` property (there is no
    # ``QueryDateTimeInfo()`` method on real pyVmomi).
    host.configManager.dateTimeSystem.dateTimeInfo = dt_info
    host.configManager.serviceSystem.serviceInfo.service = [_service("ntpd", ntpd_running)]
    return host


def test_get():
    host = _fake_host(servers=("a",), ntpd_running=True)
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        assert mod.get() == {"servers": ["a"], "enabled": True}


def test_set_servers():
    host = _fake_host(servers=("pool.ntp.org", "time.cloudflare.com"))
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        mod.set_servers(["pool.ntp.org", "time.cloudflare.com"])
    call = host.configManager.dateTimeSystem.UpdateDateTimeConfig.call_args
    assert list(call.kwargs["config"].ntpConfig.server) == ["pool.ntp.org", "time.cloudflare.com"]


def test_set_enabled():
    host = _fake_host(ntpd_running=False)
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        mod.set_enabled(False)
    host.configManager.serviceSystem.Stop.assert_called_once_with(id="ntpd")
