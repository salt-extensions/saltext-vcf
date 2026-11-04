"""Tests for OpsClient.get_pak_status."""

import pytest

from saltext.vcf.clients import ops_client as mod


@pytest.fixture
def client():
    cli = mod.OpsClient.__new__(mod.OpsClient)
    cli.requests = []

    def request(method, path, expected_status=(200,), **kwargs):
        cli.requests.append((method, path, expected_status))
        return {"cluster_pak_install_status": "COMPLETED"}

    cli.request = request
    return cli


def test_uses_pak_id_path(client):
    out = client.get_pak_status(pak_id="pak-1")
    assert out["path"] == "/casa/upgrade/cluster/pak/pak-1/status"
    assert client.requests == [("GET", "/casa/upgrade/cluster/pak/pak-1/status", (200, 202))]


def test_status_path_wins_and_never_falls_back_to_reserved(client):
    out = client.get_pak_status(
        pak_id="pak-1", pak_status_path="/casa/upgrade/cluster/pak/other/status"
    )
    assert out["path"] == "/casa/upgrade/cluster/pak/other/status"
    assert all("reserved" not in req[1] for req in client.requests)


def test_requires_an_identifier(client):
    with pytest.raises(mod.CommandExecutionError):
        client.get_pak_status()


def test_request_errors_propagate(client):
    def boom(*a, **k):
        raise RuntimeError("503")

    client.request = boom
    with pytest.raises(RuntimeError):
        client.get_pak_status(pak_id="pak-1")
