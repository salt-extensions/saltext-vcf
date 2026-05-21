"""Tests for modules.vcf_esxi_service."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from saltext.vcf.modules import vcf_esxi_service as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def _service(key, *, running=True, policy="on"):
    svc = MagicMock()
    svc.key = key
    svc.label = key
    svc.running = running
    svc.policy = policy
    return svc


def _fake_host(services=()):
    host = MagicMock()
    host.configManager.serviceSystem.serviceInfo.service = list(services)
    return host


def test_list():
    host = _fake_host([_service("TSM-SSH", running=True, policy="on")])
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        result = mod.list_()
    assert "TSM-SSH" in result
    assert result["TSM-SSH"]["state"] == "RUNNING"
    assert result["TSM-SSH"]["policy"] == "ON"


def test_get():
    host = _fake_host([_service("TSM-SSH", running=True, policy="on")])
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        result = mod.get("TSM-SSH")
    assert result["state"] == "RUNNING"
    assert result["policy"] == "ON"


@pytest.mark.parametrize(
    "fn,soap_method", [("start", "Start"), ("stop", "Stop"), ("restart", "Restart")]
)
def test_actions(fn, soap_method):
    host = _fake_host([_service("TSM-SSH")])
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        getattr(mod, fn)("TSM-SSH")
    getattr(host.configManager.serviceSystem, soap_method).assert_called_once_with(id="TSM-SSH")


def test_set_policy():
    host = _fake_host([_service("TSM-SSH", policy="automatic")])
    with patch("saltext.vcf.utils.esxi.get_host_system", return_value=host):
        mod.set_policy("TSM-SSH", "AUTOMATIC")
    host.configManager.serviceSystem.UpdatePolicy.assert_called_once_with(
        id="TSM-SSH", policy="automatic"
    )


def test_set_policy_rejects_bad_value():
    with pytest.raises(ValueError):
        mod.set_policy("TSM-SSH", "BOGUS")
