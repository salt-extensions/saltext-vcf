"""Tests for OpsPatchOrchestrator.pak_installed: upload, wait for CANDIDATE, start install."""

import pytest

from saltext.vcf.clients import ops_patch_orchestrator as mod
from saltext.vcf.clients.ops_patch_orchestrator import OpsPatchOrchestrator

PAK = "vRealizeOperationsManagerEnterprise-912025885555"


class FakeProvider:
    def __init__(
        self,
        status=None,
        uploaded_id=PAK,
        content_missing=False,
        install_error=None,
        confirmed=None,
        underway=False,
    ):
        self.underway = underway
        self.install_error = install_error
        self.confirmed = confirmed
        self.status = status
        self.content_missing = content_missing
        self.uploaded_id = uploaded_id
        self.calls = []

    def get_pak_install_status(self, pak_id):
        self.calls.append(("status", pak_id))
        return self.status

    def pak_install_underway(self, pak_id):
        self.calls.append(("underway", pak_id))
        return self.underway

    def pak_content_missing(self, pak_id):
        self.calls.append(("content_missing", pak_id))
        return self.content_missing

    def upload_and_install_pak(self, **kwargs):
        self.calls.append(("upload", kwargs))
        return {
            "pak_id": self.uploaded_id,
            "pak_status_path": f"/casa/upgrade/cluster/pak/{self.uploaded_id}/status",
        }

    def wait_for_pak_candidate(self, pak_id):
        self.calls.append(("wait_candidate", pak_id))

    def trigger_pak_install(self, pak_id, force_content_update=True):
        self.calls.append(("install", pak_id, force_content_update))
        if self.install_error:
            raise self.install_error

    def get_pak_snapshot(self, pak_id):
        self.calls.append(("snapshot", pak_id))
        return ("CANDIDATE", (("VALIDATED", "CANDIDATE", None),))

    def confirm_pak_install_started(self, pak_id, baseline=None):
        self.calls.append(("confirm", pak_id, baseline))
        return self.confirmed

    def names(self):
        return [c[0] for c in self.calls]


def orch(provider):
    return OpsPatchOrchestrator(provider, logger=None)


def test_fresh_install_uploads_waits_then_installs():
    prov = FakeProvider()
    result = orch(prov).pak_installed(pak_file="/f.pak")
    assert prov.names() == ["upload", "wait_candidate", "snapshot", "install"]
    assert result["changed"] is True
    assert result["data"]["pak_id"] == PAK
    assert result["data"]["uploaded"] is True
    assert result["data"]["install_triggered"] is True
    assert prov.calls[-1] == ("install", PAK, True)


def test_candidate_skips_upload_and_only_installs():
    prov = FakeProvider(status="CANDIDATE")
    result = orch(prov).pak_installed(pak_file="/f.pak", pak_id=PAK)
    assert prov.names() == [
        "status",
        "content_missing",
        "underway",
        "wait_candidate",
        "snapshot",
        "install",
    ]
    assert result["changed"] is True
    assert result["data"]["uploaded"] is False
    assert result["data"]["pak_status_path"] == f"/casa/upgrade/cluster/pak/{PAK}/status"


@pytest.mark.parametrize("status", ["COMPLETED", "IN_PROGRESS", "INSTALLING"])
def test_installed_or_running_is_left_alone(status):
    prov = FakeProvider(status=status)
    result = orch(prov).pak_installed(pak_file="/f.pak", pak_id=PAK)
    assert prov.names() == ["status"]
    assert result["changed"] is False
    assert result["success"] is True
    assert status in result["comment"]


def test_unknown_pak_uploads_again():
    prov = FakeProvider(status=None)
    orch(prov).pak_installed(pak_file="/f.pak", pak_id=PAK)
    assert prov.names() == ["status", "upload", "wait_candidate", "snapshot", "install"]


def test_failed_pak_uploads_again():
    prov = FakeProvider(status="FAILED")
    orch(prov).pak_installed(pak_file="/f.pak", pak_id=PAK)
    assert "upload" in prov.names()


def test_force_content_update_is_forwarded():
    prov = FakeProvider()
    orch(prov).pak_installed(pak_file="/f.pak", force_content_update=False)
    assert prov.calls[-1] == ("install", PAK, False)


def test_dry_run_touches_nothing():
    prov = FakeProvider(status="COMPLETED")
    result = orch(prov).pak_installed(pak_file="/f.pak", pak_id=PAK, dry_run=True)
    assert prov.calls == []
    assert result["changed"] is True


def test_missing_pak_id_after_upload_raises():
    prov = FakeProvider(uploaded_id=None)
    with pytest.raises(mod.CommandExecutionError, match="did not return a pak id"):
        orch(prov).pak_installed(pak_file="/f.pak")
    assert "install" not in prov.names()


def test_pak_file_required():
    with pytest.raises(mod.CommandExecutionError):
        orch(FakeProvider()).pak_installed(pak_file=None)


def test_candidate_with_undistributed_content_is_uploaded_again():
    """Regression: a CANDIDATE pak left NOT_DISTRIBUTED (for example after a revert) makes install return HTTP 500."""
    prov = FakeProvider(status="CANDIDATE", content_missing=True)
    result = orch(prov).pak_installed(pak_file="/f.pak", pak_id=PAK)
    assert prov.names() == [
        "status",
        "content_missing",
        "upload",
        "wait_candidate",
        "snapshot",
        "install",
    ]
    assert result["data"]["uploaded"] is True


def gateway_error(transient=True):
    err = mod.CommandExecutionError("POST install failed. HTTP 502. Response: Unknown")
    err.transient = transient
    return err


def test_gateway_error_is_accepted_when_install_actually_started():
    prov = FakeProvider(install_error=gateway_error(), confirmed=("IN_PROGRESS", ()))
    result = orch(prov).pak_installed(pak_file="/f.pak")
    assert prov.names()[-3:] == ["snapshot", "install", "confirm"]
    assert prov.calls[-1][2] == ("CANDIDATE", (("VALIDATED", "CANDIDATE", None),))
    assert result["success"] is True
    assert result["data"]["install_triggered"] is True
    assert "IN_PROGRESS" in result["data"]["install_note"]


def test_gateway_error_is_raised_when_install_did_not_start():
    prov = FakeProvider(install_error=gateway_error(), confirmed=None)
    with pytest.raises(mod.CommandExecutionError, match="HTTP 502"):
        orch(prov).pak_installed(pak_file="/f.pak")


def test_non_transient_error_is_not_swallowed():
    prov = FakeProvider(install_error=gateway_error(transient=False), confirmed=("IN_PROGRESS", ()))
    with pytest.raises(mod.CommandExecutionError):
        orch(prov).pak_installed(pak_file="/f.pak")
    assert "confirm" not in prov.names()


def test_candidate_pak_whose_install_is_already_underway_is_not_started_again():
    """Regression: cluster status stays CANDIDATE during the install, so a second POST must be avoided."""
    prov = FakeProvider(status="CANDIDATE", underway=True)
    result = orch(prov).pak_installed(pak_file="/f.pak", pak_id=PAK)
    assert prov.names() == ["status", "content_missing", "underway"]
    assert result["changed"] is False
    assert result["success"] is True
    assert "already underway" in result["comment"]


def test_unreachable_after_gateway_error_is_accepted_with_a_note():
    prov = FakeProvider(install_error=gateway_error(), confirmed=("UNKNOWN", ()))
    result = orch(prov).pak_installed(pak_file="/f.pak")
    assert result["success"] is True
    assert "unconfirmed" in result["data"]["install_note"]
