"""Tests for states.vcf_vcenter_custom_attribute."""

import pytest

from saltext.vcf.clients import vcenter_custom_attribute as c
from saltext.vcf.states import vcf_vcenter_custom_attribute as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_present_already_exists(monkeypatch):
    monkeypatch.setattr(
        c,
        "get_or_none",
        lambda opts, name, profile=None: {"key": 1, "name": name, "managed_object_type": None},
    )
    ret = st.present("Owner")
    assert ret["changes"] == {}


def test_present_creates(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "get_or_none", lambda opts, name, profile=None: None)
    monkeypatch.setattr(
        c,
        "add",
        lambda opts, name, managed_object_type=None, profile=None: calls.append(
            (name, managed_object_type)
        )
        or {"key": 5, "name": name, "managed_object_type": managed_object_type},
    )
    ret = st.present("Owner", managed_object_type="VirtualMachine")
    assert ret["changes"] == {
        "new": {"key": 5, "name": "Owner", "managed_object_type": "VirtualMachine"}
    }
    assert calls == [("Owner", "VirtualMachine")]


def test_present_test_mode(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda opts, name, profile=None: None)
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.present("Owner")
    assert ret["result"] is None


def test_absent_already_absent(monkeypatch):
    monkeypatch.setattr(c, "get_or_none", lambda opts, name, profile=None: None)
    ret = st.absent("Owner")
    assert ret["changes"] == {}


def test_absent_deletes(monkeypatch):
    calls = []
    monkeypatch.setattr(
        c,
        "get_or_none",
        lambda opts, name, profile=None: {"key": 7, "name": name, "managed_object_type": None},
    )
    monkeypatch.setattr(c, "remove", lambda opts, key, profile=None: calls.append(key))
    ret = st.absent("Owner")
    assert ret["changes"] == {"deleted": "Owner"}
    assert calls == [7]


def test_absent_test_mode(monkeypatch):
    monkeypatch.setattr(
        c,
        "get_or_none",
        lambda opts, name, profile=None: {"key": 7, "name": name, "managed_object_type": None},
    )
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.absent("Owner")
    assert ret["result"] is None
