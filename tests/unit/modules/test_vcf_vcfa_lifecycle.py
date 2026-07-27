"""Tests for modules.vcf_vcfa_lifecycle (patch-baseline additions)."""

import pytest

from saltext.vcf.clients import vcfa_lifecycle as c
from saltext.vcf.modules import vcf_vcfa_lifecycle as m


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(m, "__opts__", opts, raising=False)


def test_baseline_check_compliant(monkeypatch):
    monkeypatch.setattr(
        c,
        "installed_patches",
        lambda o, p, profile=None: [{"version": "9.0.1"}, {"version": "9.0.2"}],
    )
    out = m.baseline_check("p-1", ["9.0.1", "9.0.2"])
    assert out["compliant"] is True
    assert set(out["installed"]) == {"9.0.1", "9.0.2"}
    assert set(out["in_baseline"]) == {"9.0.1", "9.0.2"}
    assert out["out_of_baseline"] == []


def test_baseline_check_non_compliant(monkeypatch):
    monkeypatch.setattr(
        c,
        "installed_patches",
        lambda o, p, profile=None: [{"version": "9.0.1"}, {"version": "9.0.99"}],
    )
    out = m.baseline_check("p-1", ["9.0.1", "9.0.2"])
    assert out["compliant"] is False
    assert out["out_of_baseline"] == ["9.0.99"]
    assert out["in_baseline"] == ["9.0.1"]


def test_baseline_check_empty_installed(monkeypatch):
    monkeypatch.setattr(c, "installed_patches", lambda o, p, profile=None: [])
    out = m.baseline_check("p-1", ["9.0.1"])
    assert out["compliant"] is False
    assert out["installed"] == []


def test_installed_patch_versions_pass_through(monkeypatch):
    monkeypatch.setattr(
        c, "installed_patch_versions", lambda o, p, profile=None: ["9.0.1"]
    )
    assert m.installed_patch_versions("p-1") == ["9.0.1"]


def test_stage_patch_pass_through(monkeypatch):
    calls = []
    monkeypatch.setattr(
        c, "stage_patch", lambda o, p, v, profile=None: calls.append((p, v)) or {"id": "u"}
    )
    assert m.stage_patch("p-1", "9.0.1")["id"] == "u"
    assert calls == [("p-1", "9.0.1")]


def test_apply_patch_pass_through(monkeypatch):
    calls = []
    monkeypatch.setattr(
        c,
        "apply_patch",
        lambda o, p, v, options=None, profile=None: calls.append((p, v, options))
        or {"id": "u"},
    )
    assert m.apply_patch("p-1", "9.0.1", options={"x": True})["id"] == "u"
    assert calls == [("p-1", "9.0.1", {"x": True})]


def test_find_patch_pass_through(monkeypatch):
    monkeypatch.setattr(
        c, "find_patch", lambda o, p, v, profile=None: {"version": v}
    )
    assert m.find_patch("p-1", "9.0.1") == {"version": "9.0.1"}
