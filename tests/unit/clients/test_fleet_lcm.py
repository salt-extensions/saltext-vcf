"""Tests for clients.fleet_lcm."""

import pytest

from saltext.vcf.clients.fleet_lcm import FleetLcmClient
from saltext.vcf.clients.fleet_lcm import FleetLcmError


@pytest.fixture
def client():
    return FleetLcmClient("flt.example", "ops.example", "u", "p")


def test_requires_host():
    with pytest.raises(FleetLcmError):
        FleetLcmClient("", "ops.example", "u", "p")
    with pytest.raises(FleetLcmError):
        FleetLcmClient("flt.example", "", "u", "p")


def test_select_target_version(client):
    system = {"availableTargetVersions": [{"targetVersion": "9.1.0"}, "9.0.2"]}
    assert client.select_target_version(system) == "9.1.0"
    assert client.select_target_version(system, "9.0.2") == "9.0.2"
    with pytest.raises(FleetLcmError):
        client.select_target_version(system, "8.0")
    with pytest.raises(FleetLcmError):
        client.select_target_version({})


def test_submit_requires_task_id(client, monkeypatch):
    monkeypatch.setattr(client, "request", lambda *a, **k: {})
    with pytest.raises(FleetLcmError):
        client.configure_plan("9.1.0")


def test_apply_posts_action(client, monkeypatch):
    calls = []
    monkeypatch.setattr(
        client, "request", lambda m, p, b=None: calls.append((m, p, b)) or {"id": "t1"}
    )
    assert client.apply_upgrade("9.1.0") == "t1"
    assert calls == [("POST", "/fleet-lcm/v1/system?action=apply", {"targetVersion": "9.1.0"})]


def _scripted(client, monkeypatch, steps):
    it = iter(steps)

    def request(*_a, **_k):
        step = next(it)
        if isinstance(step, Exception):
            raise step
        return step

    monkeypatch.setattr(client, "request", request)


def test_wait_retries_unreachable_then_succeeds(client, monkeypatch):
    _scripted(
        client, monkeypatch, [{"status": "RUNNING"}, FleetLcmError("down"), {"status": "SUCCEEDED"}]
    )
    assert client.wait_for_task("t1", sleep=lambda _s: None)["status"] == "SUCCEEDED"


def test_wait_fails_on_bad_status(client, monkeypatch):
    _scripted(client, monkeypatch, [{"status": "FAILED"}])
    with pytest.raises(FleetLcmError):
        client.wait_for_task("t1", sleep=lambda _s: None)


def test_wait_times_out(client, monkeypatch):
    _scripted(client, monkeypatch, [{"status": "RUNNING"}] * 5)
    with pytest.raises(FleetLcmError):
        client.wait_for_task("t1", timeout_seconds=0, sleep=lambda _s: None)


class _Resp:
    def __init__(self, payload, status=200):
        self._payload, self.status_code, self.ok = payload, status, status < 400

    def json(self):
        return self._payload


def test_authenticate_exchanges_ops_token(client, monkeypatch):
    calls = []

    def post(url, json=None, headers=None, **_k):
        calls.append((url, json, headers))
        return _Resp({"token": "ops-t"} if "acquire" in url else {"jwtToken": "jwt-t"})

    monkeypatch.setattr(client.session, "post", post)
    assert client.authenticate() == "jwt-t"
    assert calls[0][0] == "https://ops.example/suite-api/api/auth/token/acquire"
    assert calls[0][1] == {"username": "u", "password": "p"}
    assert calls[1][0] == "https://ops.example/suite-api/api/auth/token/exchange"
    assert calls[1][1] == {"serviceKeys": ["fleet-lcm"]}
    assert calls[1][2]["Authorization"] == "OpsToken ops-t"


def test_authenticate_failure(client, monkeypatch):
    monkeypatch.setattr(client.session, "post", lambda *a, **k: _Resp({}, 401))
    with pytest.raises(FleetLcmError, match="token acquire"):
        client.authenticate()


def test_sync_depot_metadata_posts_sync_action(client, monkeypatch):
    calls = []
    monkeypatch.setattr(
        client, "request", lambda m, p, b=None: calls.append((m, p, b)) or {"id": "s1"}
    )
    assert client.sync_depot_metadata() == "s1"
    assert calls == [("POST", "/fleet-lcm/v1/depot-metadata?action=sync", None)]


def test_sync_depot_metadata_requires_task_id(client, monkeypatch):
    monkeypatch.setattr(client, "request", lambda *a, **k: {})
    with pytest.raises(FleetLcmError):
        client.sync_depot_metadata()


class _TextResp(_Resp):
    text = '{"ok": true}'


def _session_script(client, monkeypatch, statuses):
    seen = []

    def request(method, url, headers=None, **_k):
        seen.append(headers["Authorization"])
        return _TextResp({"ok": True}, statuses.pop(0))

    monkeypatch.setattr(client.session, "request", request)
    tokens = iter(["jwt-1", "jwt-2", "jwt-3"])
    monkeypatch.setattr(client, "authenticate", lambda: setattr(client, "_token", next(tokens)))
    return seen


def test_request_reauthenticates_once_on_401(client, monkeypatch):
    seen = _session_script(client, monkeypatch, [200, 401, 200])
    client.request("GET", "/a")
    assert client.request("GET", "/b") == {"ok": True}
    assert seen == ["Bearer jwt-1", "Bearer jwt-1", "Bearer jwt-2"]


def test_request_gives_up_after_one_retry_but_next_call_refreshes_again(client, monkeypatch):
    seen = _session_script(client, monkeypatch, [401, 401, 200])
    with pytest.raises(FleetLcmError, match="HTTP 401"):
        client.request("GET", "/a")
    assert client.request("GET", "/a") == {"ok": True}
    assert seen == ["Bearer jwt-1", "Bearer jwt-2", "Bearer jwt-2"]
