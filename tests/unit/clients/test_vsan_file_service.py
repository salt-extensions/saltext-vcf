"""Tests for clients.vsan_file_service (SOAP via /vsanHealth)."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from saltext.vcf.clients import vsan_file_service as c


def _cluster_with_network(net_name):
    net = MagicMock()
    net.name = net_name
    host = MagicMock()
    host.network = [net]
    cluster = MagicMock()
    cluster.host = [host]
    return cluster, net


def test_enabled_true(opts):
    cluster, _ = _cluster_with_network("VM-Mgmt")
    config = MagicMock()
    config.fileServiceConfig.enabled = True
    cs = MagicMock()
    cs.VsanClusterGetConfig.return_value = config
    with (
        patch("saltext.vcf.clients.vsan_file_service.vsan.find_cluster", return_value=cluster),
        patch("saltext.vcf.clients.vsan_file_service.vsan.cluster_config_system", return_value=cs),
    ):
        assert c.enabled(opts, "SDDC-Cluster1") is True


def test_enabled_false_when_no_config(opts):
    cluster, _ = _cluster_with_network("VM-Mgmt")
    cs = MagicMock()
    cs.VsanClusterGetConfig.return_value = None
    with (
        patch("saltext.vcf.clients.vsan_file_service.vsan.find_cluster", return_value=cluster),
        patch("saltext.vcf.clients.vsan_file_service.vsan.cluster_config_system", return_value=cs),
    ):
        assert c.enabled(opts, "SDDC-Cluster1") is False


def test_set_enabled_requires_network_name(opts):
    cluster, _ = _cluster_with_network("VM-Mgmt")
    with (
        patch("saltext.vcf.clients.vsan_file_service.vsan.find_cluster", return_value=cluster),
        patch(
            "saltext.vcf.clients.vsan_file_service.vsan.cluster_config_system",
            return_value=MagicMock(),
        ),
    ):
        with pytest.raises(ValueError):
            c.set_enabled(opts, "SDDC-Cluster1", True)


def test_set_enabled_true_submits_reconfigure(opts):
    cluster, net = _cluster_with_network("VM-Mgmt")
    cs = MagicMock()
    task = MagicMock()
    task._moId = "task-1"
    cs.VsanClusterReconfig.return_value = task
    with (
        patch("saltext.vcf.clients.vsan_file_service.vsan.find_cluster", return_value=cluster),
        patch("saltext.vcf.clients.vsan_file_service.vsan.cluster_config_system", return_value=cs),
    ):
        result = c.set_enabled(opts, "SDDC-Cluster1", True, network_name="VM-Mgmt")
    assert result == "task-1"
    spec = cs.VsanClusterReconfig.call_args.kwargs["vsanReconfigSpec"]
    assert spec.fileServiceConfig.enabled is True
    assert spec.fileServiceConfig.network is net


def test_list_domains(opts):
    cluster, _ = _cluster_with_network("VM-Mgmt")
    fs = MagicMock()
    d1, d2 = MagicMock(), MagicMock()
    d1.name = "fileshare"
    d2.name = "other"
    fs.QueryFileServiceDomains.return_value = [d1, d2]
    with (
        patch("saltext.vcf.clients.vsan_file_service.vsan.find_cluster", return_value=cluster),
        patch("saltext.vcf.clients.vsan_file_service.vsan.file_service_system", return_value=fs),
    ):
        assert c.list_domains(opts, "SDDC-Cluster1") == ["fileshare", "other"]
        assert c.domain_exists(opts, "SDDC-Cluster1", "fileshare") is True


def test_create_domain_marks_first_ip_primary(opts):
    cluster, _ = _cluster_with_network("VM-Mgmt")
    fs = MagicMock()
    task = MagicMock()
    task._moId = "task-2"
    fs.CreateFileServiceDomain.return_value = task
    with (
        patch("saltext.vcf.clients.vsan_file_service.vsan.find_cluster", return_value=cluster),
        patch("saltext.vcf.clients.vsan_file_service.vsan.file_service_system", return_value=fs),
    ):
        result = c.create_domain(
            opts,
            "SDDC-Cluster1",
            "fileshare",
            {"10.0.0.1": "f0.test", "10.0.0.2": "f1.test"},
            "255.255.255.0",
            "10.0.0.250",
            ["test"],
            ["10.0.0.250"],
        )
    assert result == "task-2"
    domain_config = fs.CreateFileServiceDomain.call_args[0][0]
    assert domain_config.fileServerIpConfig[0].isPrimary is True


def test_remove_domain(opts):
    cluster, _ = _cluster_with_network("VM-Mgmt")
    fs = MagicMock()
    task = MagicMock()
    task._moId = "task-3"
    fs.RemoveFileServiceDomain.return_value = task
    with (
        patch("saltext.vcf.clients.vsan_file_service.vsan.find_cluster", return_value=cluster),
        patch("saltext.vcf.clients.vsan_file_service.vsan.file_service_system", return_value=fs),
    ):
        result = c.remove_domain(opts, "SDDC-Cluster1", "fileshare")
    assert result == "task-3"
    fs.RemoveFileServiceDomain.assert_called_once_with("fileshare", cluster)


def test_download_ovf_uses_discovered_url_when_not_given(opts):
    cluster, _ = _cluster_with_network("VM-Mgmt")
    fs = MagicMock()
    fs.FindOvfDownloadUrl.return_value = "https://example.test/fsvm.ovf"
    task = MagicMock()
    task._moId = "task-4"
    fs.DownloadFileServiceOvf.return_value = task
    with (
        patch("saltext.vcf.clients.vsan_file_service.vsan.find_cluster", return_value=cluster),
        patch("saltext.vcf.clients.vsan_file_service.vsan.file_service_system", return_value=fs),
    ):
        result = c.download_ovf(opts, "SDDC-Cluster1")
    assert result == "task-4"
    fs.DownloadFileServiceOvf.assert_called_once_with("https://example.test/fsvm.ovf")


def test_download_ovf_raises_when_no_url_found(opts):
    cluster, _ = _cluster_with_network("VM-Mgmt")
    fs = MagicMock()
    fs.FindOvfDownloadUrl.return_value = None
    with (
        patch("saltext.vcf.clients.vsan_file_service.vsan.find_cluster", return_value=cluster),
        patch("saltext.vcf.clients.vsan_file_service.vsan.file_service_system", return_value=fs),
    ):
        with pytest.raises(RuntimeError):
            c.download_ovf(opts, "SDDC-Cluster1")
