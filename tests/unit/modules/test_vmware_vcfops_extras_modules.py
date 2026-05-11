"""Module-layer tests for the new VCF Ops execution modules."""

import pytest

from saltext.vmware.clients import vcfops_alert as al_c
from saltext.vmware.clients import vcfops_auth as au_c
from saltext.vmware.clients import vcfops_collector as col_c
from saltext.vmware.clients import vcfops_credential as cr_c
from saltext.vmware.clients import vcfops_deployment as dep_c
from saltext.vmware.clients import vcfops_maintenance as mt_c
from saltext.vmware.clients import vcfops_recommendation as re_c
from saltext.vmware.clients import vcfops_report as rp_c
from saltext.vmware.clients import vcfops_resource_group as rg_c
from saltext.vmware.clients import vcfops_solution as so_c
from saltext.vmware.clients import vcfops_supermetric as sm_c
from saltext.vmware.clients import vcfops_task as ta_c
from saltext.vmware.modules import vmware_vcfops_alert as al_m
from saltext.vmware.modules import vmware_vcfops_auth as au_m
from saltext.vmware.modules import vmware_vcfops_collector as col_m
from saltext.vmware.modules import vmware_vcfops_credential as cr_m
from saltext.vmware.modules import vmware_vcfops_deployment as dep_m
from saltext.vmware.modules import vmware_vcfops_maintenance as mt_m
from saltext.vmware.modules import vmware_vcfops_recommendation as re_m
from saltext.vmware.modules import vmware_vcfops_report as rp_m
from saltext.vmware.modules import vmware_vcfops_resource_group as rg_m
from saltext.vmware.modules import vmware_vcfops_solution as so_m
from saltext.vmware.modules import vmware_vcfops_supermetric as sm_m
from saltext.vmware.modules import vmware_vcfops_task as ta_m


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    for mod in (
        al_m,
        au_m,
        col_m,
        cr_m,
        dep_m,
        mt_m,
        re_m,
        rp_m,
        rg_m,
        so_m,
        sm_m,
        ta_m,
    ):
        monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_auth_module(monkeypatch):
    monkeypatch.setattr(au_c, "sources_list", lambda o, profile=None: [])
    monkeypatch.setattr(au_c, "roles_list", lambda o, profile=None: [])
    monkeypatch.setattr(au_c, "roles_get", lambda o, n, profile=None: {"n": n})
    monkeypatch.setattr(au_c, "roles_create", lambda o, s, profile=None: s)
    monkeypatch.setattr(au_c, "roles_delete", lambda o, n, profile=None: n)
    monkeypatch.setattr(au_c, "privileges_list", lambda o, profile=None: [])
    monkeypatch.setattr(au_c, "users_list", lambda o, profile=None: [])
    monkeypatch.setattr(au_c, "users_get", lambda o, u, profile=None: {"u": u})
    monkeypatch.setattr(au_c, "users_create", lambda o, s, profile=None: s)
    monkeypatch.setattr(au_c, "users_update", lambda o, u, s, profile=None: s)
    monkeypatch.setattr(au_c, "users_delete", lambda o, u, profile=None: u)
    monkeypatch.setattr(au_c, "usergroups_list", lambda o, profile=None: [])
    monkeypatch.setattr(au_c, "usergroups_get", lambda o, g, profile=None: {"g": g})
    monkeypatch.setattr(au_c, "usergroups_create", lambda o, s, profile=None: s)
    monkeypatch.setattr(au_c, "usergroups_delete", lambda o, g, profile=None: g)
    assert au_m.sources_list() == []
    assert au_m.roles_list() == []
    assert au_m.roles_get("Admin") == {"n": "Admin"}
    au_m.roles_create({"name": "x"})
    assert au_m.roles_delete("x") == "x"
    assert au_m.privileges_list() == []
    assert au_m.users_list() == []
    assert au_m.users_get("u-1") == {"u": "u-1"}
    au_m.users_create({"n": 1})
    au_m.users_update("u-1", {})
    assert au_m.users_delete("u-1") == "u-1"
    assert au_m.usergroups_list() == []
    assert au_m.usergroups_get("g-1") == {"g": "g-1"}
    au_m.usergroups_create({})
    assert au_m.usergroups_delete("g-1") == "g-1"


def test_collector_module(monkeypatch):
    monkeypatch.setattr(col_c, "list_", lambda o, profile=None: [])
    monkeypatch.setattr(col_c, "get", lambda o, c, profile=None: {"c": c})
    monkeypatch.setattr(col_c, "delete", lambda o, c, profile=None: c)
    monkeypatch.setattr(col_c, "groups_list", lambda o, profile=None: [])
    monkeypatch.setattr(col_c, "groups_get", lambda o, g, profile=None: {"g": g})
    monkeypatch.setattr(col_c, "groups_create", lambda o, s, profile=None: s)
    monkeypatch.setattr(col_c, "groups_update", lambda o, g, s, profile=None: s)
    monkeypatch.setattr(col_c, "groups_delete", lambda o, g, profile=None: g)
    assert col_m.list_() == []
    assert col_m.get("1") == {"c": "1"}
    assert col_m.delete("1") == "1"
    assert col_m.groups_list() == []
    assert col_m.groups_get("g") == {"g": "g"}
    col_m.groups_create({})
    col_m.groups_update("g", {})
    assert col_m.groups_delete("g") == "g"


def test_credential_module(monkeypatch):
    monkeypatch.setattr(cr_c, "list_", lambda o, profile=None: [])
    monkeypatch.setattr(cr_c, "get", lambda o, c, profile=None: {"c": c})
    monkeypatch.setattr(cr_c, "create", lambda o, s, profile=None: s)
    monkeypatch.setattr(cr_c, "update", lambda o, c, s, profile=None: s)
    monkeypatch.setattr(cr_c, "delete", lambda o, c, profile=None: c)
    monkeypatch.setattr(cr_c, "kinds_list", lambda o, profile=None: [])
    assert cr_m.list_() == []
    assert cr_m.get("c") == {"c": "c"}
    cr_m.create({})
    cr_m.update("c", {})
    assert cr_m.delete("c") == "c"
    assert cr_m.kinds_list() == []


def test_alert_active(monkeypatch):
    monkeypatch.setattr(
        al_c,
        "active_list",
        lambda o, page=0, page_size=1000, params=None: {"params": params},
    )
    monkeypatch.setattr(al_c, "active_get", lambda o, aid: {"id": aid})
    monkeypatch.setattr(al_c, "symptoms_get", lambda o, sid: {"id": sid})
    assert al_m.active_list(activeOnly=True)["params"] == {"activeOnly": True}
    assert al_m.active_list()["params"] is None
    assert al_m.active_get("a") == {"id": "a"}
    assert al_m.symptoms_get("s") == {"id": "s"}


def test_recommendation_module(monkeypatch):
    monkeypatch.setattr(re_c, "list_", lambda o, page=0, page_size=1000: [])
    monkeypatch.setattr(re_c, "get", lambda o, r: {"r": r})
    assert re_m.list_() == []
    assert re_m.get("x") == {"r": "x"}


def test_resource_group_module(monkeypatch):
    monkeypatch.setattr(rg_c, "list_", lambda o, profile=None: [])
    monkeypatch.setattr(rg_c, "get", lambda o, g, profile=None: {"g": g})
    monkeypatch.setattr(rg_c, "create", lambda o, s, profile=None: s)
    monkeypatch.setattr(rg_c, "update", lambda o, g, s, profile=None: s)
    monkeypatch.setattr(rg_c, "delete", lambda o, g, profile=None: g)
    assert rg_m.list_() == []
    assert rg_m.get("g") == {"g": "g"}
    rg_m.create({})
    rg_m.update("g", {})
    assert rg_m.delete("g") == "g"


def test_supermetric_module(monkeypatch):
    monkeypatch.setattr(sm_c, "list_", lambda o, page=0, page_size=1000: [])
    monkeypatch.setattr(sm_c, "get", lambda o, s: {"s": s})
    monkeypatch.setattr(sm_c, "create", lambda o, sp: sp)
    monkeypatch.setattr(sm_c, "update", lambda o, s, sp: sp)
    monkeypatch.setattr(sm_c, "delete", lambda o, s: s)
    assert sm_m.list_() == []
    assert sm_m.get("s") == {"s": "s"}
    sm_m.create({})
    sm_m.update("s", {})
    assert sm_m.delete("s") == "s"


def test_report_module(monkeypatch):
    monkeypatch.setattr(rp_c, "list_", lambda o, page=0, page_size=1000: [])
    monkeypatch.setattr(rp_c, "get", lambda o, r: {"r": r})
    monkeypatch.setattr(rp_c, "generate", lambda o, s: s)
    monkeypatch.setattr(rp_c, "download", lambda o, r, fmt="PDF": b"bytes")
    monkeypatch.setattr(rp_c, "delete", lambda o, r: r)
    assert rp_m.list_() == []
    assert rp_m.get("r") == {"r": "r"}
    rp_m.generate({})
    assert rp_m.download("r") == b"bytes"
    assert rp_m.delete("r") == "r"


def test_maintenance_module(monkeypatch):
    monkeypatch.setattr(mt_c, "list_", lambda o, page=0, page_size=1000: [])
    monkeypatch.setattr(mt_c, "get", lambda o, m: {"m": m})
    monkeypatch.setattr(mt_c, "create", lambda o, s: s)
    monkeypatch.setattr(mt_c, "update", lambda o, m, s: s)
    monkeypatch.setattr(mt_c, "delete", lambda o, m: m)
    assert mt_m.list_() == []
    assert mt_m.get("m") == {"m": "m"}
    mt_m.create({})
    mt_m.update("m", {})
    assert mt_m.delete("m") == "m"


def test_task_module(monkeypatch):
    monkeypatch.setattr(ta_c, "list_", lambda o, page=0, page_size=1000: [])
    monkeypatch.setattr(ta_c, "get", lambda o, t: {"t": t})
    assert ta_m.list_() == []
    assert ta_m.get("t") == {"t": "t"}


def test_solution_module(monkeypatch):
    monkeypatch.setattr(so_c, "list_", lambda o: [])
    monkeypatch.setattr(so_c, "get", lambda o, s: {"s": s})
    assert so_m.list_() == []
    assert so_m.get("s") == {"s": "s"}


def test_deployment_module(monkeypatch):
    monkeypatch.setattr(dep_c, "node_status", lambda o, profile=None: {"status": "ONLINE"})
    monkeypatch.setattr(dep_c, "applications_list", lambda o, page=0, page_size=1000: [])
    monkeypatch.setattr(dep_c, "applications_get", lambda o, a: {"a": a})
    assert dep_m.node_status() == {"status": "ONLINE"}
    assert dep_m.healthy() is True
    assert dep_m.applications_list() == []
    assert dep_m.applications_get("a") == {"a": "a"}


def test_deployment_module_unhealthy(monkeypatch):
    monkeypatch.setattr(dep_c, "node_status", lambda o, profile=None: {"status": "OFFLINE"})
    assert dep_m.healthy() is False
