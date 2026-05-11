"""Smoke tests for the SOAP exec modules — wire-up only (clients are tested separately)."""

from unittest.mock import patch

import pytest

from saltext.vmware.modules import vmware_vim_alarm
from saltext.vmware.modules import vmware_vim_extension
from saltext.vmware.modules import vmware_vim_perf


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    for mod in (vmware_vim_alarm, vmware_vim_perf, vmware_vim_extension):
        monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_alarm_module_delegates_to_client():
    with patch("saltext.vmware.modules.vmware_vim_alarm.c.list_") as fake:
        fake.return_value = []
        vmware_vim_alarm.list_()
        fake.assert_called_once()


def test_perf_module_delegates_to_client():
    with patch("saltext.vmware.modules.vmware_vim_perf.c.counters") as fake:
        fake.return_value = {}
        vmware_vim_perf.counters()
        fake.assert_called_once()


def test_extension_module_delegates_to_client():
    with patch("saltext.vmware.modules.vmware_vim_extension.c.list_") as fake:
        fake.return_value = []
        vmware_vim_extension.list_()
        fake.assert_called_once()


def test_extension_module_passes_kwargs():
    with patch("saltext.vmware.modules.vmware_vim_extension.c.register") as fake:
        vmware_vim_extension.register(
            "com.example.salt",
            "1.0.0",
            "Salt",
            "Example",
            server=[{"url": "https://example.com"}],
        )
        kwargs = fake.call_args.kwargs
        assert kwargs["server"] == [{"url": "https://example.com"}]
