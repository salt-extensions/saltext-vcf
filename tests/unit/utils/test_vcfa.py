"""Tests for saltext.vcf.utils.vcfa."""

import pytest
import responses

from saltext.vcf.utils import vcfa


def test_get_config_default(opts):
    cfg = vcfa.get_config(opts)
    assert cfg == {
        "host": "vcfa.test",
        "username": "configadmin",
        "password": "p",
        "domain": "System Domain",
        "verify_ssl": False,
        "timeout": vcfa.DEFAULT_TIMEOUT,
    }


def test_get_tokens_two_step_login(opts, vcfa_authed):
    refresh, bearer = vcfa.get_tokens(opts)
    assert refresh == "vcfa-refresh-abc"
    assert bearer == "vcfa-bearer-abc"
    csp_calls = [c for c in vcfa_authed.calls if "csp/gateway/am/api/login" in c.request.url]
    iaas_calls = [c for c in vcfa_authed.calls if "iaas/api/login" in c.request.url]
    assert len(csp_calls) == 1
    assert len(iaas_calls) == 1


def test_get_tokens_caches(opts, vcfa_authed):
    vcfa.get_tokens(opts)
    vcfa.get_tokens(opts)
    csp_calls = [c for c in vcfa_authed.calls if "csp/gateway/am/api/login" in c.request.url]
    assert len(csp_calls) == 1


def test_invalidate_token_forces_reacquire(opts, vcfa_authed):
    vcfa.get_tokens(opts)
    vcfa.invalidate_token(opts)
    vcfa.get_tokens(opts)
    csp_calls = [c for c in vcfa_authed.calls if "csp/gateway/am/api/login" in c.request.url]
    assert len(csp_calls) == 2


def test_api_get_sets_bearer(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET, "https://vcfa.test/iaas/api/projects", json={"content": []}, status=200
    )
    vcfa.api_get(opts, "/iaas/api/projects")
    auth_header = vcfa_authed.calls[-1].request.headers.get("Authorization")
    assert auth_header == "Bearer vcfa-bearer-abc"


def test_api_get_returns_parsed_json(opts, vcfa_authed):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/iaas/api/projects",
        json={"content": [{"id": "p1"}]},
        status=200,
    )
    assert vcfa.api_get(opts, "/iaas/api/projects") == {"content": [{"id": "p1"}]}


def test_api_post_sends_body(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        "https://vcfa.test/iaas/api/projects",
        json={"id": "p1"},
        status=200,
    )
    out = vcfa.api_post(opts, "/iaas/api/projects", body={"name": "p"})
    assert out == {"id": "p1"}


def test_api_call_uses_pillar_timeout(opts, vcfa_authed, monkeypatch):
    opts["pillar"]["saltext.vcf"]["vcfa"]["timeout"] = 1234
    # Prime the token cache so the patched Session.request below intercepts
    # only the data GET, not the two-step login flow.
    vcfa.get_tokens(opts)

    seen = {}
    import requests

    def fake_request(self, method, url, **kwargs):
        seen.update(kwargs)
        resp = requests.Response()
        resp.status_code = 200
        resp._content = b"{}"
        return resp

    monkeypatch.setattr(requests.Session, "request", fake_request)
    vcfa.api_get(opts, "/iaas/api/projects")
    assert seen["timeout"] == 1234


def test_401_triggers_bearer_refresh_and_retry(opts, vcfa_authed):
    vcfa_authed.add(responses.GET, "https://vcfa.test/iaas/api/projects", status=401)
    # Re-mint via iaas/api/login.
    vcfa_authed.add(
        responses.POST,
        "https://vcfa.test/iaas/api/login",
        json={"token": "vcfa-bearer-new"},
        status=200,
    )
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/iaas/api/projects",
        json={"content": []},
        status=200,
    )
    out = vcfa.api_get(opts, "/iaas/api/projects")
    assert out == {"content": []}
    # CSP login is not re-hit; refresh-token cached -> bearer-only re-mint.
    csp_calls = [c for c in vcfa_authed.calls if "csp/gateway/am/api/login" in c.request.url]
    assert len(csp_calls) == 1


def test_api_post_multipart_strips_content_type(opts, vcfa_authed):
    vcfa_authed.add(
        responses.POST,
        "https://vcfa.test/vco/api/packages",
        json={"name": "pkg"},
        status=200,
    )
    files = {"file": ("pkg.package", b"abc", "application/octet-stream")}
    out = vcfa.api_post_multipart(opts, "/vco/api/packages", files=files)
    assert out == {"name": "pkg"}
    req = vcfa_authed.calls[-1].request
    # The multipart helper must not send the JSON Content-Type that a JSON
    # call would; requests builds its own multipart boundary header.
    assert "multipart/form-data" in req.headers.get("Content-Type", "")


def test_wait_for_deployment_success(opts, vcfa_authed, monkeypatch):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/deployment/api/deployments/dep-1",
        json={"id": "dep-1", "status": "CREATE_INPROGRESS"},
        status=200,
    )
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/deployment/api/deployments/dep-1",
        json={"id": "dep-1", "status": "CREATE_SUCCESSFUL"},
        status=200,
    )
    monkeypatch.setattr(vcfa.time, "sleep", lambda s: None)
    out = vcfa.wait_for_deployment(opts, "dep-1", timeout=60, poll_interval=0)
    assert out["status"] == "CREATE_SUCCESSFUL"


def test_wait_for_deployment_failure(opts, vcfa_authed, monkeypatch):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/deployment/api/deployments/dep-1",
        json={"id": "dep-1", "status": "CREATE_FAILED"},
        status=200,
    )
    monkeypatch.setattr(vcfa.time, "sleep", lambda s: None)
    with pytest.raises(RuntimeError, match="CREATE_FAILED"):
        vcfa.wait_for_deployment(opts, "dep-1", timeout=60, poll_interval=0)


def test_wait_for_deployment_timeout(opts, vcfa_authed, monkeypatch):
    vcfa_authed.add(
        responses.GET,
        "https://vcfa.test/deployment/api/deployments/dep-1",
        json={"id": "dep-1", "status": "CREATE_INPROGRESS"},
        status=200,
    )
    # The mock returns the same in-progress on each poll; make_monotonic
    # advances time so the deadline is reached on the second iteration.
    times = iter([0.0, 100.0])
    monkeypatch.setattr(vcfa.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(vcfa.time, "sleep", lambda s: None)
    with pytest.raises(TimeoutError):
        vcfa.wait_for_deployment(opts, "dep-1", timeout=10, poll_interval=0)
