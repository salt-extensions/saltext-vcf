"""Tests for clients.vsan_fault_domain."""

from unittest.mock import MagicMock
from unittest.mock import patch

from saltext.vcf.clients import vsan_fault_domain


def _make_cluster():
    cluster = MagicMock()
    cluster._moId = "domain-c9"  # noqa: SLF001
    h1 = MagicMock()
    h1._moId = "host-1"  # noqa: SLF001
    h1.name = "esx-0-00"
    h2 = MagicMock()
    h2._moId = "host-2"  # noqa: SLF001
    h2.name = "esx-0-01"
    cluster.host = [h1, h2]
    return cluster


def test_list_returns_assignments(opts):
    """``list_`` iterates the cluster's hosts directly and reads
    ``vsanSystem.config.faultDomainInfo`` from each host.
    """
    cluster = _make_cluster()
    h1, h2 = cluster.host
    h1.configManager.vsanSystem.config.faultDomainInfo.name = "rack-A"
    h1.configManager.vsanSystem.config.clusterInfo.nodeUuid = "node-uuid-1"
    h2.configManager.vsanSystem.config.faultDomainInfo.name = ""
    h2.configManager.vsanSystem.config.clusterInfo.nodeUuid = "node-uuid-2"

    with patch(
        "saltext.vcf.clients.vsan_fault_domain.vsan.find_cluster",
        return_value=cluster,
    ):
        result = vsan_fault_domain.list_(opts, "domain-c9")

    assert result == [
        {
            "host": "esx-0-00",
            "host_id": "host-1",
            "fault_domain": "rack-A",
            "node_uuid": "node-uuid-1",
        },
        {
            "host": "esx-0-01",
            "host_id": "host-2",
            "fault_domain": None,
            "node_uuid": "node-uuid-2",
        },
    ]


def test_assign_builds_reconfig_spec(opts):
    """pyVmomi type-checks every attribute assignment, so patch the vim.*
    constructors used inside ``assign`` to return MagicMocks. We just want
    to verify the call structure, not the wire-level spec validity.
    """
    cluster = _make_cluster()
    task = MagicMock()
    task._moId = "task-77"  # noqa: SLF001

    captured = []

    def fd_spec_constructor():
        m = MagicMock()
        captured.append(m)
        return m

    with patch(
        "saltext.vcf.clients.vsan_fault_domain.vsan.find_cluster",
        return_value=cluster,
    ):
        with patch(
            "saltext.vcf.clients.vsan_fault_domain.vsan.cluster_config_system",
        ) as cs:
            cs.return_value.VsanClusterReconfig.return_value = task
            with patch(
                "saltext.vcf.clients.vsan_fault_domain.vim.cluster.VsanFaultDomainSpec",
                side_effect=fd_spec_constructor,
            ):
                with patch(
                    "saltext.vcf.clients.vsan_fault_domain.vim.cluster.VsanFaultDomainsConfigSpec"
                ):
                    with patch("saltext.vcf.clients.vsan_fault_domain.vim.vsan.ReconfigSpec"):
                        result = vsan_fault_domain.assign(
                            opts,
                            "domain-c9",
                            {"esx-0-00": "rack-A", "esx-0-01": "rack-B"},
                        )

    assert result == "task-77"
    cs.return_value.VsanClusterReconfig.assert_called_once()
    # Two distinct FD specs were constructed — one per fault domain
    assert len(captured) == 2
    names_assigned = [c.name for c in captured]
    # Names captured the values that were assigned to the mock instances
    assert set(names_assigned) == {"rack-A", "rack-B"}
