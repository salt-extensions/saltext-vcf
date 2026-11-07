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


def test_install_pak_posts_install_with_force_content_update(client):
    seen = {}

    def request(method, path, expected_status=(200,), **kwargs):
        seen.update(method=method, path=path, expected=expected_status, kwargs=kwargs)

    client.request = request
    client.install_pak("pak-1")
    assert seen["method"] == "POST"
    assert seen["path"] == "/casa/upgrade/cluster/pak/pak-1/operation/install"
    assert seen["kwargs"] == {"json": {"force_content_update": True}}
    assert 200 in seen["expected"] and 202 in seen["expected"]


def test_install_pak_force_content_update_can_be_disabled(client):
    seen = {}
    client.request = lambda method, path, expected_status=(200,), **kw: seen.update(kw)
    client.install_pak("pak-1", force_content_update=False)
    assert seen["json"] == {"force_content_update": False}


def test_install_pak_requires_id(client):
    with pytest.raises(mod.CommandExecutionError):
        client.install_pak("")


def test_gateway_errors_are_marked_transient():
    class Resp:
        status_code = 502
        text = "Unknown"

        @staticmethod
        def json():
            raise ValueError

    err = mod.OpsClient._error(Resp, "POST", "/casa/x")
    assert err.transient is True
    assert err.status_code == 502


def test_other_http_errors_are_not_transient():
    class Resp:
        status_code = 500
        text = "boom"

        @staticmethod
        def json():
            raise ValueError

    assert mod.OpsClient._error(Resp, "POST", "/casa/x").transient is False


def test_install_pak_connection_errors_are_transient(client):
    def boom(*a, **k):
        raise mod.requests.ConnectionError("reset")

    client.request = boom
    with pytest.raises(mod.CommandExecutionError) as info:
        client.install_pak("pak-1")
    assert info.value.transient is True
