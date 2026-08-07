"""Tests for clients.vcenter_statistics (SOAP via PerformanceManager)."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from saltext.vcf.clients import vcenter_statistics as c


def _interval(key, name, sampling_period, length, level, enabled):
    i = MagicMock()
    i.key = key
    i.name = name
    i.samplingPeriod = sampling_period
    i.length = length
    i.level = level
    i.enabled = enabled
    return i


def _mgr(intervals):
    mgr = MagicMock()
    mgr.historicalInterval = intervals
    return mgr


DEFAULT_INTERVALS = [
    _interval(1, "Past day", 300, 86400, 1, True),
    _interval(2, "Past week", 1800, 604800, 1, True),
    _interval(3, "Past month", 7200, 2592000, 1, True),
    _interval(4, "Past year", 86400, 31536000, 1, True),
]


def test_intervals_get_shape(opts):
    mgr = _mgr(DEFAULT_INTERVALS)
    with patch("saltext.vcf.clients.vcenter_statistics.soap.perf_manager", return_value=mgr):
        result = c.intervals_get(opts)
    assert set(result) == {"past_day", "past_week", "past_month", "past_year"}
    assert result["past_day"] == {
        "key": 1,
        "enabled": True,
        "interval_minutes": 5,
        "save_days": 1,
        "level": 1,
    }


def test_interval_get_single(opts):
    mgr = _mgr(DEFAULT_INTERVALS)
    with patch("saltext.vcf.clients.vcenter_statistics.soap.perf_manager", return_value=mgr):
        result = c.interval_get(opts, "past_year")
    assert result["save_days"] == 365


def test_interval_set_updates_only_given_fields(opts):
    mgr = _mgr(list(DEFAULT_INTERVALS))
    with patch("saltext.vcf.clients.vcenter_statistics.soap.perf_manager", return_value=mgr):
        c.interval_set(opts, "past_day", level=2)
    called = mgr.UpdatePerfInterval.call_args.kwargs["interval"]
    assert called.key == 1
    assert called.level == 2
    assert called.samplingPeriod == 300
    assert called.enabled is True


def test_interval_set_unknown_name_raises(opts):
    with pytest.raises(ValueError):
        c.interval_set(opts, "past_decade", level=2)


def test_interval_set_missing_key_raises(opts):
    mgr = _mgr([])
    with patch("saltext.vcf.clients.vcenter_statistics.soap.perf_manager", return_value=mgr):
        with pytest.raises(LookupError):
            c.interval_set(opts, "past_day", level=2)
