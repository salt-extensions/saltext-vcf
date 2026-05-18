"""Smoke tests for the SOAP exec modules — wire-up only (clients are tested separately)."""

from unittest.mock import patch

import pytest

from saltext.vcf.modules import vcf_vim_alarm
from saltext.vcf.modules import vcf_vim_extension
from saltext.vcf.modules import vcf_vim_perf


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    for mod in (vcf_vim_alarm, vcf_vim_perf, vcf_vim_extension):
        monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_alarm_module_delegates_to_client():
    with patch("saltext.vcf.modules.vcf_vim_alarm.c.list_") as fake:
        fake.return_value = []
        vcf_vim_alarm.list_()
        fake.assert_called_once()


def test_perf_module_delegates_to_client():
    with patch("saltext.vcf.modules.vcf_vim_perf.c.counters") as fake:
        fake.return_value = {}
        vcf_vim_perf.counters()
        fake.assert_called_once()


def test_extension_module_delegates_to_client():
    with patch("saltext.vcf.modules.vcf_vim_extension.c.list_") as fake:
        fake.return_value = []
        vcf_vim_extension.list_()
        fake.assert_called_once()


def test_extension_module_passes_kwargs():
    with patch("saltext.vcf.modules.vcf_vim_extension.c.register") as fake:
        vcf_vim_extension.register(
            "com.example.salt",
            "1.0.0",
            "Salt",
            "Example",
            server=[{"url": "https://example.com"}],
        )
        kwargs = fake.call_args.kwargs
        assert kwargs["server"] == [{"url": "https://example.com"}]
