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


def test_timeout_message_names_the_component_and_warns_the_task_may_still_run(client, monkeypatch):
    task = {
        "status": "RUNNING",
        "name": "OPS_UPGRADE_91",
        "updateTime": "2026-11-18T05:00:00Z",
        "description": {"args": {"componentName": "VCF Operations"}},
    }
    _scripted(client, monkeypatch, [task, task])
    ticks = iter([0, 0, 10, 10])  # first poll succeeds, the next deadline check expires
    monkeypatch.setattr("saltext.vcf.clients.fleet_lcm.time.monotonic", lambda: next(ticks))
    with pytest.raises(FleetLcmError) as exc:
        client.wait_for_task("t1", timeout_seconds=5, sleep=lambda _s: None)
    msg = str(exc.value)
    assert "component: VCF Operations" in msg and "last update: 2026-11-18T05:00:00Z" in msg
    assert "may still be running on the appliance" in msg


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


def test_wait_fails_fast_when_the_task_id_does_not_exist(client, monkeypatch):
    """A plan id mistaken for a task id returns 404 forever; do not retry for the whole timeout."""
    calls = []

    def request(method, path, body=None):
        calls.append(path)
        raise FleetLcmError("HTTP 404", status_code=404)

    monkeypatch.setattr(client, "request", request)
    with pytest.raises(FleetLcmError, match="not found.*not a task"):
        client.wait_for_task("plan-id", timeout_seconds=3600, sleep=lambda _s: None)
    assert len(calls) == 5


def test_wait_keeps_retrying_other_errors_and_resets_the_404_count(client, monkeypatch):
    _scripted(
        client,
        monkeypatch,
        [
            FleetLcmError("nf", status_code=404),
            FleetLcmError("nf", status_code=404),
            FleetLcmError("down", status_code=503),
            FleetLcmError("nf", status_code=404),
            {"status": "SUCCEEDED"},
        ],
    )
    assert client.wait_for_task("t1", sleep=lambda _s: None)["status"] == "SUCCEEDED"
