"""Tests for the VKS-extension execution modules."""

import os
import sys

import pytest

from saltext.vcf.clients import sddc_vcf_services as svc_c
from saltext.vcf.clients import vcenter_supervisor_compat as compat_c
from saltext.vcf.clients import vcenter_supervisor_kubeconfig as kc_c
from saltext.vcf.clients import vcenter_supervisor_service as svcsv_c
from saltext.vcf.clients import vcenter_supervisor_software as sw_c
from saltext.vcf.clients import vcenter_vm_class as vmc_c
from saltext.vcf.modules import vcf_vcenter_supervisor_compat as compat_m
from saltext.vcf.modules import vcf_vcenter_supervisor_service as svcsv_m
from saltext.vcf.modules import vcf_vcenter_supervisor_software as sw_m
from saltext.vcf.modules import vcf_vcenter_vm_class as vmc_m
from saltext.vcf.modules import vcf_vcf_services as vcfs_m
from saltext.vcf.modules import vcf_vks as vks_m


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    for mod in (svcsv_m, vmc_m, sw_m, compat_m, vcfs_m, vks_m):
        monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_supervisor_service_module(monkeypatch):
    monkeypatch.setattr(svcsv_c, "list_", lambda opts, profile=None: ["a"])
    monkeypatch.setattr(svcsv_c, "get", lambda opts, sid, profile=None: {"id": sid})
    monkeypatch.setattr(svcsv_c, "list_versions", lambda opts, sid, profile=None: ["v1"])
    monkeypatch.setattr(svcsv_c, "get_version", lambda opts, sid, v, profile=None: {"v": v})
    monkeypatch.setattr(svcsv_c, "create", lambda opts, spec, profile=None: spec)
    monkeypatch.setattr(svcsv_c, "activate", lambda opts, sid, profile=None: sid)
    monkeypatch.setattr(svcsv_c, "deactivate", lambda opts, sid, profile=None: sid)
    monkeypatch.setattr(svcsv_c, "delete", lambda opts, sid, profile=None: sid)
    assert svcsv_m.list_() == ["a"]
    assert svcsv_m.get("x")["id"] == "x"
    assert svcsv_m.list_versions("x") == ["v1"]
    assert svcsv_m.get_version("x", "v1") == {"v": "v1"}
    assert svcsv_m.create({"k": 1}) == {"k": 1}
    assert svcsv_m.activate("x") == "x"
    assert svcsv_m.deactivate("x") == "x"
    assert svcsv_m.delete("x") == "x"


def test_vm_class_module(monkeypatch):
    monkeypatch.setattr(vmc_c, "list_", lambda opts, profile=None: [])
    monkeypatch.setattr(vmc_c, "get", lambda opts, cid, profile=None: {"id": cid})
    monkeypatch.setattr(vmc_c, "create", lambda opts, spec, profile=None: spec)
    monkeypatch.setattr(vmc_c, "update", lambda opts, cid, spec, profile=None: spec)
    monkeypatch.setattr(vmc_c, "delete", lambda opts, cid, profile=None: cid)
    assert vmc_m.list_() == []
    assert vmc_m.get("x") == {"id": "x"}
    assert vmc_m.create({}) == {}
    assert vmc_m.update("x", {"cpu_count": 4}) == {"cpu_count": 4}
    assert vmc_m.delete("x") == "x"


def test_supervisor_software_module(monkeypatch):
    monkeypatch.setattr(sw_c, "list_", lambda opts, profile=None: [])
    monkeypatch.setattr(sw_c, "get", lambda opts, cid, profile=None: {"id": cid})
    monkeypatch.setattr(sw_c, "upgrade", lambda opts, cid, spec, profile=None: spec)
    assert sw_m.list_() == []
    assert sw_m.get("c1") == {"id": "c1"}
    assert sw_m.upgrade("c1", {"v": 1}) == {"v": 1}


def test_supervisor_compat_module(monkeypatch):
    monkeypatch.setattr(compat_c, "list_cluster_compatibility", lambda opts, profile=None: [])
    monkeypatch.setattr(compat_c, "list_dvs_compatibility", lambda opts, cid, profile=None: [])
    monkeypatch.setattr(
        compat_c,
        "list_edge_cluster_compatibility",
        lambda opts, cid, dvs, profile=None: [],
    )
    monkeypatch.setattr(compat_c, "get_cluster_size_info", lambda opts, profile=None: {})
    assert compat_m.list_cluster_compatibility() == []
    assert compat_m.list_dvs_compatibility("c") == []
    assert compat_m.list_edge_cluster_compatibility("c", "dvs") == []
    assert compat_m.get_cluster_size_info() == {}


def test_vcf_services_module(monkeypatch):
    sample = {
        "elements": [
            {"id": "u1", "name": "COMMON_SERVICES", "status": "UP"},
            {"id": "u2", "name": "LCM", "status": "DOWN"},
        ]
    }
    monkeypatch.setattr(svc_c, "list_", lambda opts, profile=None: sample)
    monkeypatch.setattr(svc_c, "get", lambda opts, sid, profile=None: sample["elements"][0])
    monkeypatch.setattr(
        svc_c,
        "get_by_name",
        lambda opts, name, profile=None: next(
            (e for e in sample["elements"] if e["name"] == name), None
        ),
    )
    assert vcfs_m.list_() == sample
    assert vcfs_m.get("u1")["name"] == "COMMON_SERVICES"
    assert vcfs_m.get_by_name("LCM")["status"] == "DOWN"
    assert vcfs_m.status_map() == {"COMMON_SERVICES": "UP", "LCM": "DOWN"}
    assert vcfs_m.healthy() is False


def test_vks_fetch_kubeconfig_writes_file(monkeypatch, tmp_path):
    monkeypatch.setattr(kc_c, "get_kubeconfig", lambda opts, cid, profile=None: "yaml-body")
    out = tmp_path / "kc.yml"
    result = vks_m.fetch_kubeconfig("c1", path=str(out))
    assert result["kubeconfig"] == "yaml-body"
    assert out.read_text() == "yaml-body"
    if sys.platform != "win32":
        # Windows ignores POSIX file mode bits beyond the read-only flag, so
        # ``chmod(path, 0o600)`` lands as 0o666. Only assert on POSIX systems.
        assert oct(out.stat().st_mode & 0o777) == "0o600"


def test_vks_fetch_kubeconfig_namespace_scoped(monkeypatch, tmp_path):
    seen = {}

    def stub(opts, ns, profile=None):
        seen["ns"] = ns
        return "ns-yaml"

    monkeypatch.setattr(kc_c, "get_kubeconfig_for_namespace", stub)
    out = tmp_path / "ns.yml"
    vks_m.fetch_kubeconfig("c1", path=str(out), namespace="ns-a")
    assert seen == {"ns": "ns-a"}
    assert out.read_text() == "ns-yaml"


def test_vks_fetch_kubeconfig_default_path(monkeypatch, tmp_path):
    # ``os.path.expanduser("~")`` checks HOME on POSIX but USERPROFILE on Windows,
    # so override both. Build the expected path the same way the module does so
    # the slash style matches on Windows (``expanduser("~/.kube")`` keeps the
    # forward slash literal even on Windows).
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setattr(kc_c, "get_kubeconfig", lambda opts, cid, profile=None: "yaml-body")
    result = vks_m.fetch_kubeconfig("c1")
    expected = os.path.join(os.path.expanduser("~/.kube"), "vks-c1.config")
    assert result["path"] == expected
    assert os.path.exists(result["path"])


def test_vks_saltext_kubernetes_available():
    # Truthy or falsy depending on environment — just ensure it returns a bool
    assert isinstance(vks_m.saltext_kubernetes_available(), bool)
