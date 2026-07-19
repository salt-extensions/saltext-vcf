"""Tests for states.vcf_esxi_vlcm."""

import pytest

from saltext.vcf.clients import esxi_vlcm as c
from saltext.vcf.states import vcf_esxi_vlcm as st


def _img(version):
    return {"base_image": {"version": version}}


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


# ---------------------------------------------------------------------------
# _first_draft_id
# ---------------------------------------------------------------------------


def test_first_draft_id_dict_keyed_by_id():
    """vAPI map-typed list responses key by draft id: {"1": {...}}."""
    assert st._first_draft_id({"1": {"creation_time": "x"}}) == "1"  # noqa: SLF001


def test_first_draft_id_list_of_dicts_with_id_field():
    assert st._first_draft_id([{"id": "draft-1"}]) == "draft-1"  # noqa: SLF001


def test_first_draft_id_list_of_bare_ids():
    assert st._first_draft_id(["draft-1"]) == "draft-1"  # noqa: SLF001


def test_first_draft_id_empty_variants():
    assert st._first_draft_id({}) is None  # noqa: SLF001
    assert st._first_draft_id([]) is None  # noqa: SLF001
    assert st._first_draft_id(None) is None  # noqa: SLF001


# ---------------------------------------------------------------------------
# depot_configured
# ---------------------------------------------------------------------------


def test_depot_configured_noop_when_existing(monkeypatch):
    monkeypatch.setattr(
        c, "offline_depot_list", lambda opts, profile=None: [{"location": "http://repo/d.zip"}]
    )
    ret = st.depot_configured("d1", location="http://repo/d.zip")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert "already configured" in ret["comment"]


def test_depot_configured_creates_offline(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "offline_depot_list", lambda opts, profile=None: [])
    monkeypatch.setattr(
        c,
        "offline_depot_create",
        lambda opts, body, profile=None: (calls.append(body), "task-1")[1],
    )
    monkeypatch.setattr(c, "wait_for_task", lambda opts, resp, **kw: {"status": "SUCCEEDED"})
    ret = st.depot_configured("d1", location="http://repo/d.zip")
    assert ret["result"] is True
    assert ret["changes"] == {"depot": "http://repo/d.zip"}
    assert calls[0]["location"] == "http://repo/d.zip"


def test_depot_configured_test_mode(monkeypatch):
    monkeypatch.setattr(st, "__opts__", {"test": True, "pillar": {}}, raising=False)
    monkeypatch.setattr(c, "offline_depot_list", lambda opts, profile=None: [])
    ret = st.depot_configured("d1", location="http://repo/d.zip")
    assert ret["result"] is None


def test_depot_configured_requires_location():
    ret = st.depot_configured("d1")
    assert ret["result"] is False
    assert "requires 'location'" in ret["comment"]


# ---------------------------------------------------------------------------
# depot_synced
# ---------------------------------------------------------------------------


def test_depot_synced_runs_sync_and_waits(monkeypatch):
    monkeypatch.setattr(c, "depot_sync", lambda opts, profile=None: "task-1")
    waited = []
    monkeypatch.setattr(
        c, "wait_for_task", lambda opts, resp, **kw: waited.append(resp) or {"status": "SUCCEEDED"}
    )
    ret = st.depot_synced("d1")
    assert ret["result"] is True
    assert ret["changes"] == {"synced": True}
    assert waited == ["task-1"]


def test_depot_synced_skipped_on_404(monkeypatch):
    monkeypatch.setattr(c, "depot_sync", lambda opts, profile=None: {"skipped": True})
    ret = st.depot_synced("d1")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert "skipped" in ret["comment"]


def test_depot_synced_test_mode(monkeypatch):
    monkeypatch.setattr(st, "__opts__", {"test": True, "pillar": {}}, raising=False)
    ret = st.depot_synced("d1")
    assert ret["result"] is None


# ---------------------------------------------------------------------------
# image_configured
# ---------------------------------------------------------------------------


def test_image_configured_noop_when_version_matches(monkeypatch):
    monkeypatch.setattr(c, "desired_image_get", lambda opts, cluster, profile=None: _img("1.0"))
    ret = st.image_configured("c1", image_spec=_img("1.0"))
    assert ret["result"] is True
    assert ret["changes"] == {}


def test_image_configured_fresh_import_validate_commit(monkeypatch):
    monkeypatch.setattr(c, "desired_image_get", lambda opts, cluster, profile=None: _img("0.9"))
    monkeypatch.setattr(c, "drafts_list", lambda opts, cluster, profile=None: [])
    monkeypatch.setattr(
        c,
        "draft_import_software_spec",
        lambda opts, cluster, image_spec, profile=None: "task-import",
    )
    monkeypatch.setattr(
        c, "draft_validate", lambda opts, cluster, draft_id, profile=None: "task-validate"
    )
    monkeypatch.setattr(
        c, "draft_commit", lambda opts, cluster, draft_id, message=None, profile=None: "task-commit"
    )
    monkeypatch.setattr(c, "wait_for_task", lambda opts, resp, **kw: {"status": "SUCCEEDED"})

    # After import, drafts_list is re-queried for the new draft id.
    state = {"calls": 0}

    def drafts_list(opts, cluster, profile=None):
        state["calls"] += 1
        if state["calls"] == 1:
            return []
        return [{"id": "draft-1"}]

    monkeypatch.setattr(c, "drafts_list", drafts_list)

    # Final desired_image_get (post-commit) must reflect the new version.
    gets = {"n": 0}

    def desired_image_get(opts, cluster, profile=None):
        gets["n"] += 1
        return {"base_image": {"version": "0.9" if gets["n"] == 1 else "1.0"}}

    monkeypatch.setattr(c, "desired_image_get", desired_image_get)

    ret = st.image_configured("c1", image_spec=_img("1.0"))
    assert ret["result"] is True
    assert ret["changes"] == {"base_image_version": {"old": "0.9", "new": "1.0"}}


def test_image_configured_fresh_import_dict_keyed_drafts_response(monkeypatch):
    """Regression: real vAPI list responses key by draft id ({"1": {...}}), not a list."""
    gets = {"n": 0}

    def desired_image_get(opts, cluster, profile=None):
        gets["n"] += 1
        return _img("0.9" if gets["n"] == 1 else "1.0")

    monkeypatch.setattr(c, "desired_image_get", desired_image_get)

    drafts_calls = {"n": 0}

    def drafts_list(opts, cluster, profile=None):
        drafts_calls["n"] += 1
        return {} if drafts_calls["n"] == 1 else {"1": {"creation_time": "x"}}

    monkeypatch.setattr(c, "drafts_list", drafts_list)
    monkeypatch.setattr(
        c, "draft_import_software_spec", lambda opts, cluster, image_spec, profile=None: "1"
    )

    validate_calls = []
    monkeypatch.setattr(
        c,
        "draft_validate",
        lambda opts, cluster, draft_id, profile=None: validate_calls.append(draft_id),
    )
    commit_calls = []
    monkeypatch.setattr(
        c,
        "draft_commit",
        lambda opts, cluster, draft_id, message=None, profile=None: commit_calls.append(draft_id),
    )
    monkeypatch.setattr(c, "wait_for_task", lambda opts, resp, **kw: {"status": "SUCCEEDED"})

    ret = st.image_configured("c1", image_spec=_img("1.0"))
    assert ret["result"] is True
    assert validate_calls == ["1"]
    assert commit_calls == ["1"]


def test_image_configured_existing_draft_delete_dict_keyed_response(monkeypatch):
    """Regression: draft_delete must get the real id, not None, from a dict-keyed response.

    First ``drafts_list`` call is the existing-draft check (finds stray
    draft "1"); second is the post-import re-query (finds the fresh
    draft "2").
    """
    monkeypatch.setattr(c, "desired_image_get", lambda opts, cluster, profile=None: _img("0.9"))

    state = {"calls": 0}

    def drafts_list(opts, cluster, profile=None):
        state["calls"] += 1
        if state["calls"] == 1:
            return {"1": {"creation_time": "x"}}
        return {"2": {"creation_time": "y"}}

    monkeypatch.setattr(c, "drafts_list", drafts_list)

    delete_calls = []
    monkeypatch.setattr(
        c,
        "draft_delete",
        lambda opts, cluster, draft_id, profile=None: delete_calls.append(draft_id),
    )
    monkeypatch.setattr(
        c, "draft_import_software_spec", lambda opts, cluster, image_spec, profile=None: "2"
    )
    validate_calls = []
    monkeypatch.setattr(
        c,
        "draft_validate",
        lambda opts, cluster, draft_id, profile=None: validate_calls.append(draft_id),
    )
    monkeypatch.setattr(
        c, "draft_commit", lambda opts, cluster, draft_id, message=None, profile=None: "t3"
    )
    monkeypatch.setattr(c, "wait_for_task", lambda opts, resp, **kw: {"status": "SUCCEEDED"})

    ret = st.image_configured("c1", image_spec=_img("1.0"), existing_draft_action="delete")
    assert delete_calls == ["1"]
    assert validate_calls == ["2"]
    assert ret["result"] is True


def test_image_configured_existing_draft_fail(monkeypatch):
    monkeypatch.setattr(c, "desired_image_get", lambda opts, cluster, profile=None: _img("0.9"))
    monkeypatch.setattr(c, "drafts_list", lambda opts, cluster, profile=None: [{"id": "draft-1"}])
    ret = st.image_configured("c1", image_spec=_img("1.0"), existing_draft_action="fail")
    assert ret["result"] is False
    assert "already has draft" in ret["comment"]


def test_image_configured_existing_draft_reuse_mismatch(monkeypatch):
    monkeypatch.setattr(c, "desired_image_get", lambda opts, cluster, profile=None: _img("0.9"))
    monkeypatch.setattr(c, "drafts_list", lambda opts, cluster, profile=None: [{"id": "draft-1"}])
    monkeypatch.setattr(
        c,
        "draft_get",
        lambda opts, cluster, draft_id, profile=None: {"software_spec": _img("0.5")},
    )
    ret = st.image_configured("c1", image_spec=_img("1.0"), existing_draft_action="reuse")
    assert ret["result"] is False
    assert "not the requested" in ret["comment"]


def test_image_configured_test_mode(monkeypatch):
    monkeypatch.setattr(st, "__opts__", {"test": True, "pillar": {}}, raising=False)
    monkeypatch.setattr(c, "desired_image_get", lambda opts, cluster, profile=None: _img("0.9"))
    monkeypatch.setattr(c, "drafts_list", lambda opts, cluster, profile=None: [])
    ret = st.image_configured("c1", image_spec=_img("1.0"))
    assert ret["result"] is None


def test_image_configured_requires_spec():
    ret = st.image_configured("c1")
    assert ret["result"] is False
    assert "requires 'image_spec'" in ret["comment"]


# ---------------------------------------------------------------------------
# policy_configured
# ---------------------------------------------------------------------------


def test_policy_configured_noop_when_matching(monkeypatch):
    monkeypatch.setattr(
        c,
        "apply_policy_get",
        lambda opts, cluster, profile=None: {"disable_hac": True, "extra_server_field": 1},
    )
    ret = st.policy_configured("c1", policy_spec={"disable_hac": True})
    assert ret["result"] is True
    assert ret["changes"] == {}


def test_policy_configured_updates_on_diff(monkeypatch):
    monkeypatch.setattr(
        c, "apply_policy_get", lambda opts, cluster, profile=None: {"disable_hac": False}
    )
    sets = []
    monkeypatch.setattr(
        c, "apply_policy_set", lambda opts, cluster, spec, profile=None: sets.append(spec)
    )
    ret = st.policy_configured("c1", policy_spec={"disable_hac": True})
    assert ret["result"] is True
    assert ret["changes"] == {"disable_hac": True}
    assert sets == [{"disable_hac": True}]


def test_policy_configured_test_mode(monkeypatch):
    monkeypatch.setattr(st, "__opts__", {"test": True, "pillar": {}}, raising=False)
    monkeypatch.setattr(
        c, "apply_policy_get", lambda opts, cluster, profile=None: {"disable_hac": False}
    )
    ret = st.policy_configured("c1", policy_spec={"disable_hac": True})
    assert ret["result"] is None


# ---------------------------------------------------------------------------
# compliance_checked / prechecked / staged / remediated
# ---------------------------------------------------------------------------


def test_compliance_checked_runs_and_waits(monkeypatch):
    calls = []
    monkeypatch.setattr(
        c,
        "compliance_scan",
        lambda opts, cluster, commit="1", hosts=None, profile=None: calls.append((commit, hosts))
        or "task-1",
    )
    monkeypatch.setattr(c, "wait_for_task", lambda opts, resp, **kw: {"status": "SUCCEEDED"})
    ret = st.compliance_checked("c1")
    assert ret["result"] is True
    assert ret["changes"] == {"compliance_scan": "SUCCEEDED"}
    assert calls == [("1", None)]


def test_compliance_checked_test_mode(monkeypatch):
    monkeypatch.setattr(st, "__opts__", {"test": True, "pillar": {}}, raising=False)
    ret = st.compliance_checked("c1")
    assert ret["result"] is None


def test_remediated_runs_and_waits(monkeypatch):
    monkeypatch.setattr(
        c, "remediate", lambda opts, cluster, accept_eula=True, profile=None: "task-1"
    )
    monkeypatch.setattr(c, "wait_for_task", lambda opts, resp, **kw: {"status": "SUCCEEDED"})
    ret = st.remediated("c1")
    assert ret["result"] is True
    assert ret["changes"] == {"remediate": "SUCCEEDED"}


def test_remediated_test_mode(monkeypatch):
    monkeypatch.setattr(st, "__opts__", {"test": True, "pillar": {}}, raising=False)
    ret = st.remediated("c1")
    assert ret["result"] is None


# ---------------------------------------------------------------------------
# reported
# ---------------------------------------------------------------------------


def test_reported_summarizes_presence(monkeypatch):
    monkeypatch.setattr(c, "last_check_result", lambda opts, cluster, profile=None: {"ok": True})
    monkeypatch.setattr(c, "apply_impact_report", lambda opts, cluster, profile=None: None)
    monkeypatch.setattr(c, "last_apply_result", lambda opts, cluster, profile=None: None)
    ret = st.reported("c1")
    assert ret["result"] is True
    assert ret["changes"] == {}
    assert "last_check=present" in ret["comment"]
    assert "apply_impact=none" in ret["comment"]
