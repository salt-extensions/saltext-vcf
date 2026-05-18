"""Tests for clients.vim_license."""

from unittest.mock import MagicMock

import pytest

from saltext.vcf.clients import vim_license


def _make_lic(key="00000-X1-Y2", name="vSphere Std", used=2, total=10):
    lic = MagicMock()
    lic.licenseKey = key
    lic.name = name
    lic.editionKey = "esx.full"
    lic.used = used
    lic.total = total
    lic.labels = []
    lic.properties = []
    return lic


@pytest.fixture
def env(monkeypatch):
    lm = MagicMock()
    lam = MagicMock()
    monkeypatch.setattr(vim_license, "_lm", lambda o, profile=None: lm)
    monkeypatch.setattr(vim_license, "_lam", lambda o, profile=None: lam)
    return {"lm": lm, "lam": lam}


def test_list_returns_dicts(opts, env):
    env["lm"].licenses = [_make_lic("A-1"), _make_lic("B-2")]
    out = vim_license.list_(opts)
    assert [l["license_key"] for l in out] == ["A-1", "B-2"]


def test_get_returns_one(opts, env):
    env["lm"].licenses = [_make_lic("A-1"), _make_lic("B-2")]
    assert vim_license.get(opts, "B-2")["license_key"] == "B-2"


def test_get_or_none(opts, env):
    env["lm"].licenses = []
    assert vim_license.get_or_none(opts, "missing") is None


def test_add(opts, env):
    env["lm"].AddLicense.return_value = _make_lic("NEW-KEY", name="added")
    out = vim_license.add(opts, "NEW-KEY")
    assert out["license_key"] == "NEW-KEY"
    env["lm"].AddLicense.assert_called_once()


def test_remove(opts, env):
    assert vim_license.remove(opts, "OLD-KEY") is True
    env["lm"].RemoveLicense.assert_called_with(licenseKey="OLD-KEY")


def test_assign(opts, env):
    env["lam"].UpdateAssignedLicense.return_value = _make_lic("KEY")
    out = vim_license.assign(opts, "host-1", "KEY", name="esx-1")
    assert out["license_key"] == "KEY"
    env["lam"].UpdateAssignedLicense.assert_called_with(
        entity="host-1", licenseKey="KEY", entityDisplayName="esx-1"
    )


def test_unassign(opts, env):
    assert vim_license.unassign(opts, "host-1") is True
    env["lam"].RemoveAssignedLicense.assert_called_with(entityId="host-1")


def test_assigned_list(opts, env):
    asgmt = MagicMock()
    asgmt.entityId = "host-1"
    asgmt.scope = ""
    asgmt.entityDisplayName = "esx-1"
    asgmt.assignedLicense = _make_lic("KEY")
    env["lam"].QueryAssignedLicenses.return_value = [asgmt]
    out = vim_license.assigned_list(opts)
    assert out[0]["entity_id"] == "host-1"
    assert out[0]["assigned_license"]["license_key"] == "KEY"
