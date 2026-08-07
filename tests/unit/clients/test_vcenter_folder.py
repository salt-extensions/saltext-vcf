"""Tests for clients.vcenter_folder (REST list/get, SOAP create/delete)."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from saltext.vcf.clients import vcenter_folder as c


def _folder(moid, name):
    f = MagicMock()
    f._moId = moid
    f.name = name
    return f


def _content_with_folders(folders):
    content = MagicMock()
    view = MagicMock()
    view.view = folders
    content.viewManager.CreateContainerView.return_value = view
    return content


def test_find_by_name_found(opts):
    content = _content_with_folders([_folder("group-v1", "Edge Services")])
    with patch("saltext.vcf.clients.vcenter_folder.soap.content", return_value=content):
        result = c.find_by_name(opts, "Edge Services")
    assert result == {"folder": "group-v1", "name": "Edge Services"}


def test_find_by_name_missing(opts):
    content = _content_with_folders([])
    with patch("saltext.vcf.clients.vcenter_folder.soap.content", return_value=content):
        result = c.find_by_name(opts, "Nope")
    assert result is None


def test_create_under_datacenter_root(opts):
    dc = MagicMock()
    dc._moId = "datacenter-1"
    dc.name = "SDDC-Datacenter"
    new_folder = _folder("group-v2", "Network Services")
    dc.vmFolder.CreateFolder.return_value = new_folder

    dc_content = _content_with_folders([dc])
    with patch("saltext.vcf.clients.vcenter_folder.soap.content", return_value=dc_content):
        result = c.create(opts, "Network Services", "VIRTUAL_MACHINE", datacenter="SDDC-Datacenter")
    assert result == "group-v2"
    dc.vmFolder.CreateFolder.assert_called_once_with(name="Network Services")


def test_create_under_parent_folder(opts):
    parent = _folder("group-v1", "Network Services")
    new_folder = _folder("group-v3", "Edge Services")
    parent.CreateFolder.return_value = new_folder

    content = _content_with_folders([parent])
    with patch("saltext.vcf.clients.vcenter_folder.soap.content", return_value=content):
        result = c.create(opts, "Edge Services", "VIRTUAL_MACHINE", parent="Network Services")
    assert result == "group-v3"
    parent.CreateFolder.assert_called_once_with(name="Edge Services")


def test_create_missing_datacenter_raises(opts):
    content = _content_with_folders([])
    with patch("saltext.vcf.clients.vcenter_folder.soap.content", return_value=content):
        with pytest.raises(ValueError):
            c.create(opts, "Edge Services", "VIRTUAL_MACHINE")


def test_delete_calls_destroy(opts):
    folder = _folder("group-v1", "Edge Services")
    task = MagicMock()
    folder.Destroy_Task.return_value = task

    content = _content_with_folders([folder])
    with (
        patch("saltext.vcf.clients.vcenter_folder.soap.content", return_value=content),
        patch("saltext.vcf.clients.vcenter_folder.soap.wait_for_task") as wait_mock,
    ):
        c.delete(opts, "group-v1")
    folder.Destroy_Task.assert_called_once()
    wait_mock.assert_called_once_with(task)


def test_delete_missing_raises(opts):
    content = _content_with_folders([])
    with patch("saltext.vcf.clients.vcenter_folder.soap.content", return_value=content):
        with pytest.raises(LookupError):
            c.delete(opts, "group-v9")
