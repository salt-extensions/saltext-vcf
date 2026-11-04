"""Tests for modules.vcf_ops_patch."""

import pytest

from saltext.vcf.modules import vcf_ops_patch as mod


class FakeOrch:
    last = None

    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def _fn(**kwargs):
            self.calls.append((name, kwargs))
            return {"success": True}

        return _fn


@pytest.fixture
def orch(monkeypatch):
    fake = FakeOrch()
    monkeypatch.setattr(mod, "_orch", lambda **kw: fake)
    monkeypatch.setattr(mod, "__salt__", {}, raising=False)
    return fake


@pytest.fixture
def pillar(monkeypatch):
    def _set(section):
        monkeypatch.setattr(
            mod,
            "__salt__",
            {"pillar.get": lambda key, default=None: section if key == "ops_patch" else default},
            raising=False,
        )

    return _set


def test_virtual():
    assert mod.__virtual__() == "vcf_ops_patch"


def test_connection_requires_host(monkeypatch):
    monkeypatch.setattr(mod, "__salt__", {}, raising=False)
    with pytest.raises(Exception):
        mod._connection({"username": "u", "password": "p"})


def test_connection_normalizes_overrides(monkeypatch):
    monkeypatch.setattr(mod, "__salt__", {}, raising=False)
    conn = mod._connection(
        {"host": "ops.test", "username": "u", "password": "p", "protocol": "ftp", "port": "8443"}
    )
    assert conn["protocol"] == "https"
    assert conn["port"] == 8443
    assert conn["verify_ssl"] is False


def test_download_pak_defaults(orch):
    mod.download_pak(pak_source="http://r/x.pak", destination="/tmp/x.pak")
    name, kw = orch.calls[0]
    assert name == "pak_downloaded"
    assert kw["pak_source"] == "http://r/x.pak"
    assert kw["download_timeout"] == 1800
    assert kw["dry_run"] is False


def test_download_pak_reads_pillar(orch, pillar):
    pillar(
        {
            "pak": {"source": "http://p/y.pak", "destination": "/d/y.pak"},
            "lifecycle": {"download_timeout_seconds": "99"},
        }
    )
    mod.download_pak()
    kw = orch.calls[0][1]
    assert kw["pak_source"] == "http://p/y.pak"
    assert kw["destination"] == "/d/y.pak"
    assert kw["download_timeout"] == 99


def test_install_pak_defaults(orch, pillar):
    pillar({"pak": {"destination": "/d/y.pak"}})
    mod.install_pak(dry_run="true")
    kw = orch.calls[0][1]
    assert kw["pak_file"] == "/d/y.pak"
    assert kw["pak_handling_advice"] == "CLOBBER"
    assert kw["install_timeout"] == 7200
    assert kw["dry_run"] is True


def test_wait_for_upgrade_overrides(orch):
    mod.wait_for_upgrade(timeout_seconds=10, poll_interval_seconds=2)
    name, kw = orch.calls[0]
    assert name == "upgrade_monitored"
    assert kw["timeout_seconds"] == 10
    assert kw["poll_interval_seconds"] == 2


def test_wait_for_cluster_online_defaults(orch):
    mod.wait_for_cluster_online()
    assert orch.calls[0][1]["timeout_seconds"] == 7200


def test_full_upgrade_defaults(orch):
    mod.full_upgrade(dry_run=True)
    name, kw = orch.calls[0]
    assert name == "full_upgrade"
    assert kw["monitor"] is True
    assert kw["validate_health"] is True
    assert kw["dry_run"] is True


def test_validate_and_report(orch):
    mod.validate_cluster_health(dry_run=True)
    mod.report()
    assert [c[0] for c in orch.calls] == ["cluster_health_validated", "reported"]


def test_pak_installed_alias(orch):
    mod.pak_installed(pak_file="/f.pak")
    assert orch.calls[0][0] == "pak_installed"


def test_wait_for_upgrade_uses_pak_recorded_by_install(orch, monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "__opts__", {"cachedir": str(tmp_path)}, raising=False)

    class Installer(FakeOrch):
        def pak_installed(self, **kw):
            return {
                "data": {
                    "pak_id": "pak-1",
                    "pak_status_path": "/casa/upgrade/cluster/pak/pak-1/status",
                }
            }

    monkeypatch.setattr(mod, "_orch", lambda **kw: Installer())
    mod.install_pak(pak_file="/f.pak")

    monkeypatch.setattr(mod, "_orch", lambda **kw: orch)
    mod.wait_for_upgrade()
    kw = orch.calls[0][1]
    assert kw["pak_id"] == "pak-1"
    assert kw["pak_status_path"] == "/casa/upgrade/cluster/pak/pak-1/status"


def test_wait_for_upgrade_explicit_pak_id_wins(orch, monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "__opts__", {"cachedir": str(tmp_path)}, raising=False)
    mod.wait_for_upgrade(pak_id="explicit")
    assert orch.calls[0][1]["pak_id"] == "explicit"


def test_install_pak_dry_run_records_nothing(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "__opts__", {"cachedir": str(tmp_path)}, raising=False)
    monkeypatch.setattr(mod, "__salt__", {}, raising=False)

    class Installer(FakeOrch):
        def pak_installed(self, **kw):
            return {"data": {"pak_id": "pak-1"}}

    monkeypatch.setattr(mod, "_orch", lambda **kw: Installer())
    mod.install_pak(pak_file="/f.pak", dry_run=True)
    assert not list(tmp_path.iterdir())
