"""Tests for clients.ovftool_deploy."""

from unittest import mock

import pytest

from saltext.vcf.clients import ovftool_deploy


def test_build_command_maps_common_deploy_options():
    cmd = ovftool_deploy._build_command(
        ova_source="/tmp/installer.ova",
        target_host="10.0.0.1",
        target_user="root",
        target_password="p@ss word",
        target_port=443,
        vm_name="vcf-installer",
        datastore="datastore1",
        network_map={"Network 1": "VM Network"},
        ovf_properties={"ROOT_PASSWORD": "secret"},
        disk_provisioning="thin",
        deployment_option="small",
        power_on=True,
        verify_ssl=False,
        ovftool_path="/opt/ovftool/ovftool",
        extra_args=["--X:logLevel=verbose"],
    )

    assert cmd == [
        "/opt/ovftool/ovftool",
        "--acceptAllEulas",
        "--noSSLVerify",
        "--datastore=datastore1",
        "--diskMode=thin",
        "--deploymentOption=small",
        "--name=vcf-installer",
        "--powerOn",
        "--net:Network 1=VM Network",
        "--prop:ROOT_PASSWORD=secret",
        "--X:logLevel=verbose",
        "/tmp/installer.ova",
        "vi://root:p%40ss%20word@10.0.0.1/",
    ]


def test_build_command_keeps_non_default_target_port():
    cmd = ovftool_deploy._build_command(
        ova_source="/tmp/installer.ova",
        target_host="esx.lab",
        target_user="root",
        target_password="pw",
        target_port=8443,
        vm_name="vm",
        datastore=None,
        network_map=None,
        ovf_properties=None,
        disk_provisioning=None,
        deployment_option=None,
        power_on=False,
        verify_ssl=True,
        ovftool_path="ovftool",
        extra_args=None,
    )

    assert "--noSSLVerify" not in cmd
    assert "--powerOn" not in cmd
    assert cmd[-1] == "vi://root:pw@esx.lab:8443/"


def test_deploy_ova_runs_ovftool_and_returns_result(monkeypatch):
    proc = mock.MagicMock(returncode=0, stdout="Completed successfully", stderr="")
    run = mock.MagicMock(return_value=proc)
    monkeypatch.setattr(ovftool_deploy.subprocess, "run", run)
    monkeypatch.setattr(ovftool_deploy.shutil, "which", lambda _name: "/usr/bin/ovftool")

    result = ovftool_deploy.deploy_ova(
        ova_source="/tmp/installer.ova",
        target_host="10.0.0.1",
        target_user="root",
        target_password="pw",
        vm_name="vm",
        datastore="datastore1",
        power_on=False,
    )

    assert result["backend"] == "ovftool"
    assert result["vm_name"] == "vm"
    assert result["powered_on"] is False
    assert result["returncode"] == 0
    run.assert_called_once()
    assert run.call_args.kwargs["timeout"] == 7200


def test_deploy_ova_raises_on_nonzero_exit(monkeypatch):
    proc = mock.MagicMock(returncode=1, stdout="out", stderr="err")
    monkeypatch.setattr(ovftool_deploy.subprocess, "run", mock.MagicMock(return_value=proc))
    monkeypatch.setattr(ovftool_deploy.shutil, "which", lambda _name: "/usr/bin/ovftool")

    with pytest.raises(RuntimeError, match="ovftool deployment failed"):
        ovftool_deploy.deploy_ova(
            ova_source="/tmp/installer.ova",
            target_host="10.0.0.1",
            target_user="root",
            target_password="pw",
            vm_name="vm",
        )


def test_resolve_ovftool_raises_when_missing(monkeypatch):
    monkeypatch.setattr(ovftool_deploy.shutil, "which", lambda _name: None)
    with pytest.raises(FileNotFoundError):
        ovftool_deploy._resolve_ovftool("ovftool")
