"""Tests for the vim_datastore_file state module."""

import pytest

from saltext.vmware.clients import vim_datastore_file as c
from saltext.vmware.states import vmware_vim_datastore_file as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def test_file_present_idempotent(monkeypatch):
    monkeypatch.setattr(
        c, "list_", lambda o, dc, ds, path="", profile=None: [{"path": "vsphere.iso"}]
    )
    monkeypatch.setattr(c, "upload", lambda *a, **kw: pytest.fail("should not upload"))
    ret = st.file_present("iso", "DC", "datastore-1", "iso/vsphere.iso", "/tmp/v.iso")
    assert ret["changes"] == {}


def test_file_present_uploads_when_missing(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "list_", lambda o, dc, ds, path="", profile=None: [])
    monkeypatch.setattr(c, "upload", lambda *a, **kw: calls.append(a) or 200)
    ret = st.file_present("iso", "DC", "datastore-1", "iso/vsphere.iso", "/tmp/v.iso")
    assert ret["changes"] == {"uploaded": "iso/vsphere.iso"}
    assert calls[0][-2:] == ("/tmp/v.iso", "iso/vsphere.iso")


def test_file_present_test_mode(monkeypatch, opts):
    opts["test"] = True
    monkeypatch.setattr(c, "list_", lambda o, dc, ds, path="", profile=None: [])
    monkeypatch.setattr(c, "upload", lambda *a, **kw: pytest.fail("should not upload"))
    ret = st.file_present("iso", "DC", "datastore-1", "iso/vsphere.iso", "/tmp/v.iso")
    assert ret["result"] is None


def test_file_absent_idempotent(monkeypatch):
    monkeypatch.setattr(c, "list_", lambda o, dc, ds, path="", profile=None: [])
    monkeypatch.setattr(c, "delete", lambda *a, **kw: pytest.fail("should not delete"))
    ret = st.file_absent("iso", "DC", "datastore-1", "iso/vsphere.iso")
    assert ret["changes"] == {}


def test_file_absent_deletes_when_present(monkeypatch):
    calls = []
    monkeypatch.setattr(
        c, "list_", lambda o, dc, ds, path="", profile=None: [{"path": "vsphere.iso"}]
    )
    monkeypatch.setattr(c, "delete", lambda *a, **kw: calls.append(a))
    ret = st.file_absent("iso", "DC", "datastore-1", "iso/vsphere.iso")
    assert ret["changes"] == {"deleted": "iso/vsphere.iso"}


def test_directory_present_creates(monkeypatch):
    calls = []
    monkeypatch.setattr(c, "list_", lambda o, dc, ds, path="", profile=None: [])
    monkeypatch.setattr(c, "mkdir", lambda *a, **kw: calls.append(a) or True)
    ret = st.directory_present("iso", "DC", "datastore-1", "iso")
    assert ret["changes"] == {"created": "iso"}


def test_directory_present_idempotent(monkeypatch):
    monkeypatch.setattr(c, "list_", lambda o, dc, ds, path="", profile=None: [{"path": "iso"}])
    monkeypatch.setattr(c, "mkdir", lambda *a, **kw: pytest.fail("should not mkdir"))
    ret = st.directory_present("iso", "DC", "datastore-1", "iso")
    assert ret["changes"] == {}
