"""Tests for clients.vim_vm_guest (GuestOperationsManager)."""

from datetime import datetime
from datetime import timezone
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from saltext.vcf.clients import vim_vm_guest


def _process(pid, name="bash", owner="root", cmd_line="bash -c x", end_time=None, exit_code=None):
    p = MagicMock()
    p.pid = pid
    p.name = name
    p.owner = owner
    p.cmdLine = cmd_line
    p.startTime = datetime(2026, 5, 10, tzinfo=timezone.utc)
    p.exitCode = exit_code
    p.endTime = end_time
    return p


@pytest.fixture
def factories(monkeypatch):
    state = {
        "vm": MagicMock(_moId="vm-100", name="web-01"),
        "pm": MagicMock(),
        "fm": MagicMock(),
    }
    gmgr = MagicMock()
    gmgr.processManager = state["pm"]
    gmgr.fileManager = state["fm"]
    monkeypatch.setattr(vim_vm_guest, "_vm", lambda o, v, profile=None: state["vm"])
    monkeypatch.setattr(vim_vm_guest, "_guest_mgr", lambda o, profile=None: gmgr)
    return state


# ---------- processes ----------


def test_run_command_returns_pid(factories, opts):
    factories["pm"].StartProgramInGuest.return_value = 4242
    pid = vim_vm_guest.run_command(
        opts, "vm-100", "/bin/echo", arguments="hello", username="root", password="x"
    )
    assert pid == 4242
    call = factories["pm"].StartProgramInGuest.call_args
    spec = call.kwargs["spec"]
    assert spec.programPath == "/bin/echo"
    assert spec.arguments == "hello"
    assert call.kwargs["vm"] is factories["vm"]
    assert call.kwargs["auth"].username == "root"
    assert call.kwargs["auth"].password == "x"


def test_run_command_with_env_and_cwd(factories, opts):
    factories["pm"].StartProgramInGuest.return_value = 1
    vim_vm_guest.run_command(
        opts,
        "vm-100",
        "/usr/bin/env",
        username="root",
        password="x",
        working_directory="/opt",
        env={"FOO": "bar", "BAZ": "1"},
    )
    spec = factories["pm"].StartProgramInGuest.call_args.kwargs["spec"]
    assert spec.workingDirectory == "/opt"
    assert sorted(spec.envVariables) == ["BAZ=1", "FOO=bar"]


def test_list_processes_returns_dicts(factories, opts):
    factories["pm"].ListProcessesInGuest.return_value = [
        _process(100, name="sshd"),
        _process(
            101, name="bash", exit_code=0, end_time=datetime(2026, 5, 10, 1, tzinfo=timezone.utc)
        ),
    ]
    result = vim_vm_guest.list_processes(opts, "vm-100", username="root", password="x")
    assert len(result) == 2
    assert result[0]["pid"] == 100
    assert result[1]["exit_code"] == 0
    assert result[1]["end_time"].startswith("2026-05-10T01")


def test_list_processes_with_pid_filter(factories, opts):
    factories["pm"].ListProcessesInGuest.return_value = [_process(100)]
    vim_vm_guest.list_processes(opts, "vm-100", username="root", password="x", pids=[100, 101])
    call = factories["pm"].ListProcessesInGuest.call_args
    assert call.kwargs["pids"] == [100, 101]


def test_terminate_process(factories, opts):
    vim_vm_guest.terminate_process(opts, "vm-100", 4242, username="root", password="x")
    factories["pm"].TerminateProcessInGuest.assert_called_once()
    assert factories["pm"].TerminateProcessInGuest.call_args.kwargs["pid"] == 4242


def test_read_environment(factories, opts):
    factories["pm"].ReadEnvironmentVariableInGuest.return_value = ["PATH=/bin"]
    out = vim_vm_guest.read_environment(
        opts, "vm-100", username="root", password="x", names=["PATH"]
    )
    assert out == ["PATH=/bin"]
    call = factories["pm"].ReadEnvironmentVariableInGuest.call_args
    assert call.kwargs["names"] == ["PATH"]


# ---------- files ----------


def test_upload_file_uses_returned_url(factories, opts, tmp_path):
    factories["fm"].InitiateFileTransferToGuest.return_value = "https://esxi/path?ticket=abc"
    src = tmp_path / "local.sh"
    src.write_bytes(b"#!/bin/sh\necho hi\n")

    fake_resp = MagicMock()
    fake_resp.__enter__.return_value = fake_resp
    fake_resp.__exit__.return_value = False
    fake_resp.read.return_value = b""
    with patch(
        "saltext.vcf.clients.vim_vm_guest.urllib.request.urlopen", return_value=fake_resp
    ) as urlopen:
        url = vim_vm_guest.upload_file(
            opts,
            "vm-100",
            str(src),
            "/root/remote.sh",
            username="root",
            password="x",
        )
    assert url == "https://esxi/path?ticket=abc"
    # urlopen should have been called once with a PUT request
    request = urlopen.call_args.args[0]
    assert request.method == "PUT"
    assert request.full_url == "https://esxi/path?ticket=abc"

    # Spec params
    call = factories["fm"].InitiateFileTransferToGuest.call_args
    assert call.kwargs["guestFilePath"] == "/root/remote.sh"
    assert call.kwargs["fileSize"] == src.stat().st_size
    assert call.kwargs["overwrite"] is True
    assert call.kwargs["fileAttributes"].permissions == 0o644


def test_download_file_writes_local(factories, opts, tmp_path):
    info = MagicMock()
    info.url = "https://esxi/dl?ticket=def"
    info.size = 5
    factories["fm"].InitiateFileTransferFromGuest.return_value = info

    fake_resp = MagicMock()
    fake_resp.__enter__.return_value = fake_resp
    fake_resp.__exit__.return_value = False
    fake_resp.read.return_value = b"hello"
    dst = tmp_path / "got.txt"
    with patch(
        "saltext.vcf.clients.vim_vm_guest.urllib.request.urlopen", return_value=fake_resp
    ):
        size = vim_vm_guest.download_file(
            opts,
            "vm-100",
            "/root/log",
            str(dst),
            username="root",
            password="x",
        )
    assert size == 5
    assert dst.read_bytes() == b"hello"


def test_list_files_returns_dicts(factories, opts):
    info = MagicMock()
    entry = MagicMock(
        path="a.txt", size=42, modification=datetime(2026, 5, 10, tzinfo=timezone.utc)
    )
    entry.type = "file"
    info.files = [entry]
    factories["fm"].ListFilesInGuest.return_value = info
    result = vim_vm_guest.list_files(
        opts, "vm-100", "/root", username="root", password="x", pattern="*.txt"
    )
    assert len(result) == 1
    assert result[0]["path"] == "a.txt"
    assert result[0]["size"] == 42
    assert result[0]["modification_time"].startswith("2026-05-10")
    call = factories["fm"].ListFilesInGuest.call_args
    assert call.kwargs["matchPattern"] == "*.txt"


def test_delete_file(factories, opts):
    vim_vm_guest.delete_file(opts, "vm-100", "/root/old.txt", username="root", password="x")
    factories["fm"].DeleteFileInGuest.assert_called_once()
    assert factories["fm"].DeleteFileInGuest.call_args.kwargs["filePath"] == "/root/old.txt"


def test_make_directory(factories, opts):
    vim_vm_guest.make_directory(
        opts,
        "vm-100",
        "/opt/app/etc",
        username="root",
        password="x",
        create_parents=True,
    )
    call = factories["fm"].MakeDirectoryInGuest.call_args
    assert call.kwargs["directoryPath"] == "/opt/app/etc"
    assert call.kwargs["createParentDirectories"] is True


def test_delete_directory(factories, opts):
    vim_vm_guest.delete_directory(
        opts, "vm-100", "/tmp/build", username="root", password="x", recursive=True
    )
    call = factories["fm"].DeleteDirectoryInGuest.call_args
    assert call.kwargs["directoryPath"] == "/tmp/build"
    assert call.kwargs["recursive"] is True


def test_move_file_passes_overwrite(factories, opts):
    vim_vm_guest.move_file(
        opts,
        "vm-100",
        "/a",
        "/b",
        username="root",
        password="x",
        overwrite=True,
    )
    call = factories["fm"].MoveFileInGuest.call_args
    assert call.kwargs["srcFilePath"] == "/a"
    assert call.kwargs["dstFilePath"] == "/b"
    assert call.kwargs["overwrite"] is True
