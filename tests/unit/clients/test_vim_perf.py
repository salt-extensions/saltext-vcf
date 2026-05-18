"""Tests for clients.vim_perf."""

from datetime import datetime
from datetime import timezone
from unittest.mock import MagicMock
from unittest.mock import patch

from saltext.vcf.clients import vim_perf


def test_counters_returns_dict(opts):
    counter = MagicMock()
    counter.key = 1
    counter.groupInfo.key = "cpu"
    counter.nameInfo.key = "usage"
    counter.unitInfo.key = "percent"
    counter.rollupType = "average"
    counter.statsType = "rate"
    counter.level = 1
    pm = MagicMock()
    pm.perfCounter = [counter]
    with patch("saltext.vcf.clients.vim_perf.soap.perf_manager", return_value=pm):
        result = vim_perf.counters(opts)
    assert result == {
        1: {
            "group": "cpu",
            "name": "usage",
            "unit": "percent",
            "rollup_type": "average",
            "stats_type": "rate",
            "level": 1,
        }
    }


def test_available_metrics(opts):
    m = MagicMock(counterId=1, instance="*")
    pm = MagicMock()
    pm.QueryAvailablePerfMetric.return_value = [m]
    with patch("saltext.vcf.clients.vim_perf.soap.perf_manager", return_value=pm):
        with patch(
            "saltext.vcf.clients.vim_perf.soap.get_service_instance",
            return_value=MagicMock(),
        ):
            result = vim_perf.available_metrics(opts, "vm-1")
    assert result == [{"counter_id": 1, "instance": "*"}]


def test_query_builds_querySpec(opts):  # noqa: N802  pylint: disable=invalid-name
    sample = MagicMock()
    sample.timestamp = datetime(2026, 5, 10, tzinfo=timezone.utc)
    sample.interval = 20
    val = MagicMock(id=MagicMock(counterId=1, instance=""), value=[42])
    result = MagicMock(entity=MagicMock(_moId="vm-1"), sampleInfo=[sample], value=[val])
    pm = MagicMock()
    pm.QueryPerf.return_value = [result]
    with patch("saltext.vcf.clients.vim_perf.soap.perf_manager", return_value=pm):
        with patch(
            "saltext.vcf.clients.vim_perf.soap.get_service_instance",
            return_value=MagicMock(),
        ):
            out = vim_perf.query(opts, "vm-1", [1], max_samples=10)
    assert out[0]["entity"] == "vm-1"
    assert out[0]["sample_times"] == ["2026-05-10T00:00:00+00:00"]
    assert out[0]["interval_seconds"] == [20]
    assert out[0]["values"][0]["counter_id"] == 1


def test_last_n_seconds_passes_time_window(opts):
    pm = MagicMock()
    pm.QueryPerf.return_value = []
    with patch("saltext.vcf.clients.vim_perf.soap.perf_manager", return_value=pm):
        with patch(
            "saltext.vcf.clients.vim_perf.soap.get_service_instance",
            return_value=MagicMock(),
        ):
            vim_perf.last_n_seconds(opts, "vm-1", [1], seconds=60)
    spec = pm.QueryPerf.call_args.kwargs["querySpec"][0]
    assert spec.startTime is not None
    assert spec.endTime is not None
    assert (spec.endTime - spec.startTime).total_seconds() == 60
