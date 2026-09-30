"""Tests for the vcf_vim_vm_migrate.relocate state."""

import pytest

from saltext.vcf.clients import vim_vm as vm_c
from saltext.vcf.clients import vim_vm_migrate as c
from saltext.vcf.states import vcf_vim_vm_migrate as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_already_on_target(monkeypatch):
    monkeypatch.setattr(
        vm_c, "runtime", lambda o, v, profile=None: {"host": "host-1", "datastores": ["ds1"]}
    )
    ret = st.relocate("vm-100", new_host_name="host-1", datastore_name="ds1")
    assert ret["changes"] == {}
    assert "already" in ret["comment"]


def test_relocates_when_drift(monkeypatch):
    monkeypatch.setattr(
        vm_c, "runtime", lambda o, v, profile=None: {"host": "host-9", "datastores": ["ds9"]}
    )
    called = {}

    def _relocate(o, v, **kw):
        called.update(kw)

    monkeypatch.setattr(c, "relocate", _relocate)
    ret = st.relocate("vm-100", new_host_name="host-1", datastore_name="ds1")
    assert ret["result"] is True
    assert called == {"host": "host-1", "datastore": "ds1", "profile": None}


def test_test_mode(monkeypatch):
    monkeypatch.setattr(
        vm_c, "runtime", lambda o, v, profile=None: {"host": "host-9", "datastores": ["ds9"]}
    )
    monkeypatch.setattr(st, "__opts__", {"test": True}, raising=False)
    ret = st.relocate("vm-100", new_host_name="host-1")
    assert ret["result"] is None
