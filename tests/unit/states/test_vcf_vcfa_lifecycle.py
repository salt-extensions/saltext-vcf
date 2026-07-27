"""Tests for states.vcf_vcfa_lifecycle (patch-baseline management)."""

from unittest.mock import MagicMock

import pytest
import requests

from saltext.vcf.clients import vcfa_lifecycle as c
from saltext.vcf.states import vcf_vcfa_lifecycle as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def _http_error(status):
    resp = requests.Response()
    resp.status_code = status
    exc = requests.HTTPError(f"{status}")
    exc.response = resp
    return exc


# ---------------------------------------------------------------------------
# baseline_check
# ---------------------------------------------------------------------------


def test_baseline_check_requires_allowed_versions():
    ret = st.baseline_check("audit", product="p-1")
    assert ret["result"] is False
    assert "requires 'allowed_versions'" in ret["comment"]


def test_baseline_check_reads_allowed_from_pillar(monkeypatch, opts):
    opts["pillar"]["saltext.vcf"]["vcfa_lifecycle"] = {
        "baselines": {"p-1": ["9.0.1"]}
    }
    monkeypatch.setattr(st, "__opts__", opts, raising=False)
    monkeypatch.setattr(
        c, "installed_patches", lambda o, p, profile=None: [{"version": "9.0.1"}]
    )
    ret = st.baseline_check("audit", product="p-1")
    assert ret["result"] is True


def test_baseline_check_compliant(monkeypatch):
    monkeypatch.setattr(
        c,
        "installed_patches",
        lambda o, p, profile=None: [{"version": "9.0.1"}, {"version": "9.0.2"}],
    )
    ret = st.baseline_check(
        "audit", product="p-1", allowed_versions=["9.0.1", "9.0.2"]
    )
    assert ret["result"] is True
    assert "within baseline" in ret["comment"]
    assert set(ret["pchanges"]["in_baseline"]) == {"9.0.1", "9.0.2"}
    assert ret["pchanges"]["out_of_baseline"] == []


def test_baseline_check_non_compliant(monkeypatch):
    monkeypatch.setattr(
        c,
        "installed_patches",
        lambda o, p, profile=None: [{"version": "9.0.1"}, {"version": "9.0.99"}],
    )
    ret = st.baseline_check(
        "audit", product="p-1", allowed_versions=["9.0.1", "9.0.2"]
    )
    assert ret["result"] is False
    assert "out of baseline" in ret["comment"]
    assert ret["pchanges"]["out_of_baseline"] == ["9.0.99"]


def test_baseline_check_no_installed_patches(monkeypatch):
    monkeypatch.setattr(c, "installed_patches", lambda o, p, profile=None: [])
    ret = st.baseline_check("audit", product="p-1", allowed_versions=["9.0.1"])
    assert ret["result"] is False
    assert "no installed patches" in ret["comment"]


def test_baseline_check_client_error_soft_fails(monkeypatch):
    def boom(*a, **kw):
        raise RuntimeError("gateway down")

    monkeypatch.setattr(c, "installed_patches", boom)
    ret = st.baseline_check("audit", product="p-1", allowed_versions=["9.0.1"])
    assert ret["result"] is False
    assert "gateway down" in ret["comment"]


def test_baseline_check_defaults_product_to_name(monkeypatch):
    seen = {}

    def _installed(o, p, profile=None):
        seen["product"] = p
        return [{"version": "9.0.1"}]

    monkeypatch.setattr(c, "installed_patches", _installed)
    ret = st.baseline_check("p-1", allowed_versions=["9.0.1"])
    assert ret["result"] is True
    assert seen["product"] == "p-1"


# ---------------------------------------------------------------------------
# patch_present
# ---------------------------------------------------------------------------


def test_patch_present_requires_allowed_versions():
    ret = st.patch_present("apply", product="p-1")
    assert ret["result"] is False


def test_patch_present_already_compliant(monkeypatch):
    monkeypatch.setattr(
        c, "installed_patches", lambda o, p, profile=None: [{"version": "9.0.2"}]
    )
    apply_mock = MagicMock()
    monkeypatch.setattr(c, "apply_patch", apply_mock)
    ret = st.patch_present("apply", product="p-1", allowed_versions=["9.0.1", "9.0.2"])
    assert ret["result"] is True
    assert "already at allowed patch level" in ret["comment"]
    apply_mock.assert_not_called()


def test_patch_present_applies_target(monkeypatch):
    monkeypatch.setattr(
        c, "installed_patches", lambda o, p, profile=None: [{"version": "9.0.0"}]
    )
    monkeypatch.setattr(
        c,
        "available_patches",
        lambda o, p, profile=None: [{"version": "9.0.1"}, {"version": "9.0.2"}],
    )
    calls = []
    monkeypatch.setattr(
        c,
        "apply_patch",
        lambda o, prod, ver, profile=None: calls.append((prod, ver))
        or {"id": "u-1", "state": "RUNNING"},
    )
    ret = st.patch_present(
        "apply", product="p-1", allowed_versions=["9.0.1", "9.0.2"]
    )
    assert ret["result"] is True
    # Highest-allowed-that-is-available == 9.0.2
    assert calls == [("p-1", "9.0.2")]
    assert ret["changes"]["target"] == "9.0.2"
    assert ret["changes"]["upgrade"]["id"] == "u-1"


def test_patch_present_test_mode(monkeypatch):
    monkeypatch.setattr(st, "__opts__", {"test": True, "pillar": {}}, raising=False)
    monkeypatch.setattr(
        c, "installed_patches", lambda o, p, profile=None: [{"version": "9.0.0"}]
    )
    monkeypatch.setattr(
        c, "available_patches", lambda o, p, profile=None: [{"version": "9.0.2"}]
    )
    apply_mock = MagicMock()
    monkeypatch.setattr(c, "apply_patch", apply_mock)
    ret = st.patch_present("apply", product="p-1", allowed_versions=["9.0.2"])
    assert ret["result"] is None
    assert "would apply patch" in ret["comment"]
    apply_mock.assert_not_called()


def test_patch_present_explicit_target_wins(monkeypatch):
    monkeypatch.setattr(
        c, "installed_patches", lambda o, p, profile=None: [{"version": "9.0.0"}]
    )
    monkeypatch.setattr(
        c,
        "available_patches",
        lambda o, p, profile=None: [{"version": "9.0.1"}, {"version": "9.0.2"}],
    )
    calls = []
    monkeypatch.setattr(
        c,
        "apply_patch",
        lambda o, prod, ver, profile=None: calls.append((prod, ver))
        or {"id": "u-x"},
    )
    ret = st.patch_present(
        "apply",
        product="p-1",
        allowed_versions=["9.0.1", "9.0.2"],
        target_version="9.0.1",
    )
    assert ret["result"] is True
    assert calls == [("p-1", "9.0.1")]


def test_patch_present_soft_fails_on_upgrade_404(monkeypatch):
    """Some VCFA builds ship the read side of LCM but not the write side."""
    monkeypatch.setattr(
        c, "installed_patches", lambda o, p, profile=None: [{"version": "9.0.0"}]
    )
    monkeypatch.setattr(
        c, "available_patches", lambda o, p, profile=None: [{"version": "9.0.2"}]
    )

    def _apply(*a, **kw):
        raise _http_error(404)

    monkeypatch.setattr(c, "apply_patch", _apply)
    ret = st.patch_present("apply", product="p-1", allowed_versions=["9.0.2"])
    assert ret["result"] is False
    assert "out of baseline" in ret["comment"]
    assert "out-of-band" in ret["comment"]
    assert ret["pchanges"]["needed"] == "9.0.2"


def test_patch_present_hard_fails_on_other_error(monkeypatch):
    monkeypatch.setattr(
        c, "installed_patches", lambda o, p, profile=None: [{"version": "9.0.0"}]
    )
    monkeypatch.setattr(
        c, "available_patches", lambda o, p, profile=None: [{"version": "9.0.2"}]
    )

    def _apply(*a, **kw):
        raise _http_error(500)

    monkeypatch.setattr(c, "apply_patch", _apply)
    ret = st.patch_present("apply", product="p-1", allowed_versions=["9.0.2"])
    assert ret["result"] is False


def test_patch_present_no_available_falls_back_to_last_allowed(monkeypatch):
    monkeypatch.setattr(
        c, "installed_patches", lambda o, p, profile=None: [{"version": "9.0.0"}]
    )
    monkeypatch.setattr(c, "available_patches", lambda o, p, profile=None: [])
    calls = []
    monkeypatch.setattr(
        c,
        "apply_patch",
        lambda o, prod, ver, profile=None: calls.append((prod, ver))
        or {"id": "u-fb"},
    )
    ret = st.patch_present(
        "apply", product="p-1", allowed_versions=["9.0.1", "9.0.2"]
    )
    assert ret["result"] is True
    assert calls == [("p-1", "9.0.2")]


# ---------------------------------------------------------------------------
# _pick_target
# ---------------------------------------------------------------------------


def test_pick_target_prefers_last_available():
    entries = [{"version": "9.0.1"}, {"version": "9.0.2"}]
    assert st._pick_target(["9.0.0", "9.0.1", "9.0.2"], entries) == "9.0.2"


def test_pick_target_falls_back_to_last_allowed():
    entries = [{"version": "9.9.9"}]
    assert st._pick_target(["9.0.1", "9.0.2"], entries) == "9.0.2"


def test_pick_target_no_allowed():
    assert st._pick_target([], []) is None
