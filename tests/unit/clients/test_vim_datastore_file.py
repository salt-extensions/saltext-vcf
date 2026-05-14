"""Tests for clients.vim_datastore_file."""

from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

import pytest
import responses
from pyVmomi import vim

from saltext.vmware.clients import vim_datastore_file


@pytest.fixture
def env(monkeypatch):
    dc = MagicMock()
    dc.name = "DC"
    dc._moId = "datacenter-1"  # noqa: SLF001
    ds = MagicMock()
    ds.name = "datastore-1"
    ds._moId = "ds-1"  # noqa: SLF001
    fm = MagicMock()
    file_info = MagicMock()
    file_info.path = "vsphere.iso"
    file_info.fileSize = 1234
    file_info.modification.isoformat = lambda: "2026-05-12T00:00:00+00:00"
    file_info.owner = "admin"
    search_result = MagicMock()
    search_result.file = [file_info]
    search_task = MagicMock()
    search_task.info.state = vim.TaskInfo.State.success
    search_task.info.result = search_result
    ds.browser.SearchDatastore_Task.return_value = search_task
    delete_task = MagicMock(_moId="task-del")
    move_task = MagicMock(_moId="task-mv")
    fm.DeleteDatastoreFile_Task.return_value = delete_task
    fm.MoveDatastoreFile_Task.return_value = move_task

    monkeypatch.setattr(vim_datastore_file, "_find_datacenter", lambda opts, n, profile=None: dc)
    monkeypatch.setattr(vim_datastore_file, "_find_datastore", lambda opts, n, profile=None: ds)
    monkeypatch.setattr(vim_datastore_file, "_file_manager", lambda opts, profile=None: fm)
    return {"dc": dc, "ds": ds, "fm": fm}


def test_list_returns_mapped_entries(opts, env):
    out = vim_datastore_file.list_(opts, "DC", "datastore-1")
    assert len(out) == 1
    assert out[0]["path"] == "vsphere.iso"
    assert out[0]["size"] == 1234


def test_delete_invokes_filemanager(opts, env):
    assert vim_datastore_file.delete(opts, "DC", "datastore-1", "vsphere.iso") == "task-del"
    env["fm"].DeleteDatastoreFile_Task.assert_called_once()
    kwargs = env["fm"].DeleteDatastoreFile_Task.call_args.kwargs
    assert kwargs["name"] == "[datastore-1] vsphere.iso"
    assert kwargs["datacenter"] is env["dc"]


def test_mkdir_invokes_make_directory(opts, env):
    assert vim_datastore_file.mkdir(opts, "DC", "datastore-1", "iso") is True
    env["fm"].MakeDirectory.assert_called_once()
    kwargs = env["fm"].MakeDirectory.call_args.kwargs
    assert kwargs["name"] == "[datastore-1] iso"
    assert kwargs["createParentDirectories"] is True


def test_move_cross_datastore(opts, env):
    out = vim_datastore_file.move(opts, "DC", "datastore-1", "a.iso", "DC", "datastore-2", "b.iso")
    assert out == "task-mv"
    kwargs = env["fm"].MoveDatastoreFile_Task.call_args.kwargs
    assert kwargs["sourceName"] == "[datastore-1] a.iso"
    assert kwargs["destinationName"] == "[datastore-2] b.iso"


def test_upload_streams_via_https_put(opts, env, monkeypatch):
    monkeypatch.setattr(
        "saltext.vmware.clients.vim_datastore_file.vc_rest.get_config",
        lambda o, profile=None: {"host": "vc.test", "verify_ssl": False},
    )
    monkeypatch.setattr(
        "saltext.vmware.clients.vim_datastore_file.soap.session_cookie",
        lambda o, profile=None: "vmware_soap_session=abc",
    )
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            responses.PUT,
            "https://vc.test/folder/iso/vsphere.iso",
            status=200,
        )
        with patch("builtins.open", mock_open(read_data=b"hello")):
            status = vim_datastore_file.upload(
                opts, "DC", "datastore-1", "/tmp/vsphere.iso", "iso/vsphere.iso"
            )
        assert status == 200
        # Confirm the URL had the dcPath and dsName params
        assert "dcPath=DC" in rsps.calls[-1].request.url
        assert "dsName=datastore-1" in rsps.calls[-1].request.url
        assert rsps.calls[-1].request.headers.get("Cookie") == "vmware_soap_session=abc"


def test_download_streams_via_https_get(opts, env, monkeypatch, tmp_path):
    monkeypatch.setattr(
        "saltext.vmware.clients.vim_datastore_file.vc_rest.get_config",
        lambda o, profile=None: {"host": "vc.test", "verify_ssl": False},
    )
    monkeypatch.setattr(
        "saltext.vmware.clients.vim_datastore_file.soap.session_cookie",
        lambda o, profile=None: "vmware_soap_session=abc",
    )
    out = tmp_path / "downloaded.iso"
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            responses.GET,
            "https://vc.test/folder/iso/vsphere.iso",
            body=b"hello-bytes",
            status=200,
        )
        n = vim_datastore_file.download(opts, "DC", "datastore-1", "iso/vsphere.iso", str(out))
    assert n == len(b"hello-bytes")
    assert out.read_bytes() == b"hello-bytes"
