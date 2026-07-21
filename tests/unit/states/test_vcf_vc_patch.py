"""Tests for states.vcf_vc_patch."""

import pytest

from saltext.vcf.clients import vc_patch as c
from saltext.vcf.states import vcf_vc_patch as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


# ---------------------------------------------------------------------------
# repository_configured
# ---------------------------------------------------------------------------


def test_repository_configured_requires_url():
    ret = st.repository_configured("r1")
    assert ret["result"] is False
    assert "requires 'repository_url'" in ret["comment"]


def test_repository_configured_calls_set_update_policy(monkeypatch):
    calls = []
    monkeypatch.setattr(
        c,
        "set_update_policy",
        lambda opts, url, **kw: calls.append((url, kw)) or {"ok": True},
    )
    ret = st.repository_configured("r1", repository_url="http://repo/vcsa/")
    assert ret["result"] is True
    assert calls[0][0] == "http://repo/vcsa/"


def test_repository_configured_test_mode(monkeypatch):
    monkeypatch.setattr(st, "__opts__", {"test": True, "pillar": {}}, raising=False)
    ret = st.repository_configured("r1", repository_url="http://repo/vcsa/")
    assert ret["result"] is None


def test_repository_configured_redacts_password_from_changes(monkeypatch):
    """Regression: VAMI's policy-set response can echo the repo password back."""
    monkeypatch.setattr(
        c,
        "set_update_policy",
        lambda opts, url, **kw: {"policy": {"password": "s3cret", "auto_stage": False}},
    )
    ret = st.repository_configured(
        "r1", repository_url="http://repo/vcsa/", repo_password="s3cret"
    )
    assert ret["result"] is True
    assert ret["changes"]["response"]["policy"]["password"] == "REDACTED"
    assert ret["changes"]["response"]["policy"]["auto_stage"] is False
    assert "s3cret" not in str(ret["changes"])


# ---------------------------------------------------------------------------
# _redact
# ---------------------------------------------------------------------------


def test_redact_top_level_password_key():
    out = st._redact({"password": "s3cret", "other": "keep"})  # noqa: SLF001
    assert out == {"password": "REDACTED", "other": "keep"}


def test_redact_nested_password_key():
    out = st._redact({"policy": {"password": "s3cret", "auto_stage": False}})  # noqa: SLF001
    assert out == {"policy": {"password": "REDACTED", "auto_stage": False}}


def test_redact_user_data_vmdir_password_entry():
    """VAMI install requests carry the SSO password as a user_data 'value', not a
    'password'-named key -- must be caught by the key-name check on the sibling 'key'
    field, not the generic key-name pass."""
    out = st._redact(  # noqa: SLF001
        {"user_data": [{"key": "vmdir.password", "value": "s3cret"}], "component": "lcm"}
    )
    assert out == {
        "user_data": [{"key": "vmdir.password", "value": "REDACTED"}],
        "component": "lcm",
    }


def test_redact_leaves_non_sensitive_values_untouched():
    out = st._redact({"a": 1, "b": [1, 2, {"c": "d"}], "e": None})  # noqa: SLF001
    assert out == {"a": 1, "b": [1, 2, {"c": "d"}], "e": None}


# ---------------------------------------------------------------------------
# update_prepared
# ---------------------------------------------------------------------------


def test_update_prepared_idempotent_when_already_staged(monkeypatch):
    monkeypatch.setattr(
        c,
        "resolve_update_version",
        lambda opts, **kw: ("9.0", None, {"version": "9.0"}),
    )
    monkeypatch.setattr(
        c, "get_staged_update", lambda opts, profile=None: {"value": {"version": "9.0"}}
    )
    monkeypatch.setattr(c, "staged_matches", lambda staged, version=None: True)
    stage_calls = []
    monkeypatch.setattr(c, "stage", lambda *a, **kw: stage_calls.append(1))

    ret = st.update_prepared("p1", version="9.0")
    assert ret["result"] is True
    assert "already staged" in ret["comment"]
    assert stage_calls == []


def test_update_prepared_stages_when_not_staged(monkeypatch):
    monkeypatch.setattr(
        c, "resolve_update_version", lambda opts, **kw: ("9.0", None, {"version": "9.0"})
    )
    monkeypatch.setattr(c, "get_staged_update", lambda opts, profile=None: {})
    monkeypatch.setattr(c, "staged_matches", lambda staged, version=None: False)
    stage_calls = []
    monkeypatch.setattr(
        c, "stage", lambda opts, version, component=None, profile=None: stage_calls.append(version)
    )

    ret = st.update_prepared("p1", version="9.0", monitor=False, run_precheck=False)
    assert ret["result"] is True
    assert stage_calls == ["9.0"]
    assert ret["changes"]["resolved_version"] == "9.0"


def test_update_prepared_redacts_password_when_setting_repository_policy(monkeypatch):
    """Regression: the real (non-test) set_update_policy call here has the same
    password-echo risk as repository_configured's."""
    monkeypatch.setattr(
        c, "resolve_update_version", lambda opts, **kw: ("9.0", None, {"version": "9.0"})
    )
    monkeypatch.setattr(c, "get_staged_update", lambda opts, profile=None: {})
    monkeypatch.setattr(c, "staged_matches", lambda staged, version=None: False)
    monkeypatch.setattr(
        c,
        "set_update_policy",
        lambda opts, url, **kw: {"policy": {"password": "s3cret"}},
    )
    monkeypatch.setattr(c, "stage", lambda opts, version, component=None, profile=None: "staged")

    ret = st.update_prepared(
        "p1", repository_url="http://repo/vcsa/", version="9.0", monitor=False, run_precheck=False
    )
    assert ret["result"] is True
    assert ret["changes"]["repository_policy"]["policy"]["password"] == "REDACTED"
    assert "s3cret" not in str(ret["changes"])


def test_update_prepared_force_stage_bypasses_idempotency(monkeypatch):
    monkeypatch.setattr(
        c, "resolve_update_version", lambda opts, **kw: ("9.0", None, {"version": "9.0"})
    )
    monkeypatch.setattr(
        c, "get_staged_update", lambda opts, profile=None: {"value": {"version": "9.0"}}
    )
    monkeypatch.setattr(c, "staged_matches", lambda staged, version=None: True)
    stage_calls = []
    monkeypatch.setattr(
        c, "stage", lambda opts, version, component=None, profile=None: stage_calls.append(version)
    )

    ret = st.update_prepared(
        "p1", version="9.0", monitor=False, run_precheck=False, force_stage=True
    )
    assert ret["result"] is True
    assert stage_calls == ["9.0"]


def test_update_prepared_test_mode(monkeypatch):
    monkeypatch.setattr(st, "__opts__", {"test": True, "pillar": {}}, raising=False)
    monkeypatch.setattr(
        c, "resolve_update_version", lambda opts, **kw: ("9.0", None, {"version": "9.0"})
    )
    monkeypatch.setattr(c, "get_staged_update", lambda opts, profile=None: {})
    monkeypatch.setattr(c, "staged_matches", lambda staged, version=None: False)
    ret = st.update_prepared("p1", version="9.0")
    assert ret["result"] is None


def test_update_prepared_test_mode_never_mutates_repository_policy(monkeypatch):
    """Regression: test=True must not actually PUT the repository policy."""
    monkeypatch.setattr(st, "__opts__", {"test": True, "pillar": {}}, raising=False)
    monkeypatch.setattr(
        c, "resolve_update_version", lambda opts, **kw: ("9.0", None, {"version": "9.0"})
    )
    monkeypatch.setattr(c, "get_staged_update", lambda opts, profile=None: {})
    monkeypatch.setattr(c, "staged_matches", lambda staged, version=None: False)

    def fail_if_called(*a, **kw):
        raise AssertionError("set_update_policy must not be called under test=True")

    monkeypatch.setattr(c, "set_update_policy", fail_if_called)

    ret = st.update_prepared("p1", repository_url="http://repo/vcsa/", version="9.0")
    assert ret["result"] is None


def test_update_prepared_stage_timeout_falls_back_to_wait(monkeypatch):
    monkeypatch.setattr(
        c, "resolve_update_version", lambda opts, **kw: ("9.0", None, {"version": "9.0"})
    )
    monkeypatch.setattr(c, "get_staged_update", lambda opts, profile=None: {})
    monkeypatch.setattr(c, "staged_matches", lambda staged, version=None: False)

    def raise_stage_timeout(*a, **kw):
        raise RuntimeError("Timeout happens while waiting for task out file")

    monkeypatch.setattr(c, "stage", raise_stage_timeout)
    monkeypatch.setattr(c, "is_stage_timeout_error", lambda exc: True)
    wait_calls = []
    monkeypatch.setattr(
        c,
        "wait_for_staged_update",
        lambda opts, **kw: wait_calls.append(kw) or {"success": True},
    )

    ret = st.update_prepared("p1", version="9.0", monitor=False, run_precheck=False)
    assert ret["result"] is True
    assert len(wait_calls) == 1


def test_update_prepared_stage_error_not_timeout_propagates(monkeypatch):
    monkeypatch.setattr(
        c, "resolve_update_version", lambda opts, **kw: ("9.0", None, {"version": "9.0"})
    )
    monkeypatch.setattr(c, "get_staged_update", lambda opts, profile=None: {})
    monkeypatch.setattr(c, "staged_matches", lambda staged, version=None: False)

    def raise_other(*a, **kw):
        raise RuntimeError("some other failure")

    monkeypatch.setattr(c, "stage", raise_other)
    monkeypatch.setattr(c, "is_stage_timeout_error", lambda exc: False)

    ret = st.update_prepared("p1", version="9.0", monitor=False, run_precheck=False)
    assert ret["result"] is False
    assert "some other failure" in ret["comment"]


def test_update_prepared_precheck_retries_while_staging_in_progress(monkeypatch):
    monkeypatch.setattr(
        c, "resolve_update_version", lambda opts, **kw: ("9.0", None, {"version": "9.0"})
    )
    monkeypatch.setattr(c, "get_staged_update", lambda opts, profile=None: {})
    monkeypatch.setattr(c, "staged_matches", lambda staged, version=None: False)
    monkeypatch.setattr(c, "stage", lambda opts, version, component=None, profile=None: "staged")

    attempts = {"n": 0}

    def precheck(*_a, **_kw):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise RuntimeError("precheck.not_allowed_error")
        return {"result": "ok"}

    monkeypatch.setattr(c, "precheck", precheck)
    monkeypatch.setattr(
        c, "is_staging_in_progress_error", lambda exc: "not_allowed_error" in str(exc)
    )
    monkeypatch.setattr(c, "monitor_stage", lambda opts, **kw: {"success": True})

    ret = st.update_prepared("p1", version="9.0", monitor=False, run_precheck=True)
    assert ret["result"] is True
    assert attempts["n"] == 2
    assert ret["changes"]["precheck"] == {"result": "ok"}


# ---------------------------------------------------------------------------
# update_installed
# ---------------------------------------------------------------------------


def test_update_installed_requires_sso_password():
    ret = st.update_installed("i1", version="9.0")
    assert ret["result"] is False
    assert "sso_password" in ret["comment"]


def test_update_installed_runs_and_monitors(monkeypatch):
    monkeypatch.setattr(
        c, "resolve_update_version", lambda opts, **kw: ("9.0", None, {"version": "9.0"})
    )
    install_calls = []
    monkeypatch.setattr(
        c,
        "install",
        lambda opts, version, sso_password, component=None, profile=None: install_calls.append(
            (version, sso_password)
        ),
    )
    monkeypatch.setattr(c, "monitor_install", lambda opts, **kw: {"success": True})

    ret = st.update_installed("i1", version="9.0", sso_password="s3cret")
    assert ret["result"] is True
    assert install_calls == [("9.0", "s3cret")]


def test_update_installed_redacts_sso_password_from_changes(monkeypatch):
    """Regression: an install response echoing its own user_data must not leak
    the SSO admin password into ret['changes']."""
    monkeypatch.setattr(
        c, "resolve_update_version", lambda opts, **kw: ("9.0", None, {"version": "9.0"})
    )
    monkeypatch.setattr(
        c,
        "install",
        lambda opts, version, sso_password, component=None, profile=None: {
            "user_data": [{"key": "vmdir.password", "value": sso_password}]
        },
    )
    monkeypatch.setattr(c, "monitor_install", lambda opts, **kw: {"success": True})

    ret = st.update_installed("i1", version="9.0", sso_password="s3cret")
    assert ret["result"] is True
    assert ret["changes"]["install"]["user_data"][0]["value"] == "REDACTED"
    assert "s3cret" not in str(ret["changes"])


def test_update_installed_test_mode(monkeypatch):
    monkeypatch.setattr(st, "__opts__", {"test": True, "pillar": {}}, raising=False)
    monkeypatch.setattr(
        c, "resolve_update_version", lambda opts, **kw: ("9.0", None, {"version": "9.0"})
    )
    ret = st.update_installed("i1", version="9.0", sso_password="s3cret")
    assert ret["result"] is None


# ---------------------------------------------------------------------------
# installed (composite dispatcher)
# ---------------------------------------------------------------------------


def test_installed_dispatches_to_update_prepared_in_test_mode(monkeypatch):
    monkeypatch.setattr(st, "__opts__", {"test": True, "pillar": {}}, raising=False)
    monkeypatch.setattr(
        c, "resolve_update_version", lambda opts, **kw: ("9.0", None, {"version": "9.0"})
    )
    monkeypatch.setattr(c, "get_staged_update", lambda opts, profile=None: {})
    monkeypatch.setattr(c, "staged_matches", lambda staged, version=None: False)

    # This is the exact kwarg superset the reference's buggy installed.sls example passes —
    # confirms the fixed signature accepts monitor/stage_timeout_seconds/install_timeout_seconds
    # together without raising TypeError.
    ret = st.installed(
        "vc_update_installed",
        repository_url="http://repo/vcsa/",
        version="9.0",
        sso_password="s3cret",
        component=None,
        monitor=True,
        stage_timeout_seconds=3600,
        install_timeout_seconds=7200,
    )
    assert ret["result"] is None


def test_installed_dispatches_to_update_installed_for_real_run(monkeypatch):
    monkeypatch.setattr(
        c, "resolve_update_version", lambda opts, **kw: ("9.0", None, {"version": "9.0"})
    )
    install_calls = []
    monkeypatch.setattr(
        c,
        "install",
        lambda opts, version, sso_password, component=None, profile=None: install_calls.append(
            version
        ),
    )
    monkeypatch.setattr(c, "monitor_install", lambda opts, **kw: {"success": True})

    ret = st.installed(
        "vc_update_installed",
        version="9.0",
        sso_password="s3cret",
        monitor=True,
        stage_timeout_seconds=3600,
        install_timeout_seconds=7200,
    )
    assert ret["result"] is True
    assert install_calls == ["9.0"]
