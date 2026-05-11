"""Framework-interface tests for resources.esxi."""

import json

import responses

from saltext.vmware.resources import esxi as ex

KEY = ex.CONTEXT_KEY


def test_discover(framework_opts):
    assert sorted(ex.discover(framework_opts)) == ["esxi-01", "esxi-02"]


def test_init_initialized_shutdown(monkeypatch, framework_opts):
    ctx = {}
    monkeypatch.setattr(ex, "__context__", ctx, raising=False)
    assert ex.initialized() is False
    ex.init(framework_opts)
    assert ex.initialized() is True
    assert "esxi-01" in ctx[KEY]["instances"]
    ex.shutdown(framework_opts)
    assert KEY not in ctx


def test_ping_ok(inject_resource_dunders, framework_opts, mocked_responses):
    instances = framework_opts["pillar"]["resources"]["esxi"]["instances"]
    inject_resource_dunders(ex, "esxi-01", KEY, instances)
    mocked_responses.add(responses.POST, "https://esxi.test/api/session", json="tok", status=200)
    assert ex.ping() is True


def test_ping_failure(inject_resource_dunders, framework_opts, mocked_responses):
    instances = framework_opts["pillar"]["resources"]["esxi"]["instances"]
    inject_resource_dunders(ex, "esxi-01", KEY, instances)
    mocked_responses.add(responses.POST, "https://esxi.test/api/session", status=401)
    assert ex.ping() is False


def test_service_list(inject_resource_dunders, framework_opts, esxi_authed):
    instances = framework_opts["pillar"]["resources"]["esxi"]["instances"]
    inject_resource_dunders(ex, "esxi-01", KEY, instances)
    esxi_authed.add(
        responses.GET,
        "https://esxi.test/api/esx/services",
        json=[{"name": "TSM-SSH"}],
        status=200,
    )
    assert ex.service_list() == [{"name": "TSM-SSH"}]


def test_ntp_set_servers(inject_resource_dunders, framework_opts, esxi_authed):
    instances = framework_opts["pillar"]["resources"]["esxi"]["instances"]
    inject_resource_dunders(ex, "esxi-01", KEY, instances)
    esxi_authed.add(responses.PATCH, "https://esxi.test/api/esx/ntp", status=204)
    ex.ntp_set_servers(["pool.ntp.org"])
    body = json.loads(esxi_authed.calls[-1].request.body)
    assert body == {"servers": ["pool.ntp.org"]}


def test_other_instance_targets_other_host(
    inject_resource_dunders, framework_opts, mocked_responses
):
    """Switching __resource__ to esxi-02 routes calls to the second host."""
    instances = framework_opts["pillar"]["resources"]["esxi"]["instances"]
    inject_resource_dunders(ex, "esxi-02", KEY, instances)
    mocked_responses.add(responses.POST, "https://esxi02.test/api/session", json="t", status=200)
    mocked_responses.add(
        responses.GET,
        "https://esxi02.test/api/esx/host",
        json={"version": "8.0"},
        status=200,
    )
    assert ex.host_info() == {"version": "8.0"}


def test_grains_includes_host_info(inject_resource_dunders, framework_opts, esxi_authed):
    instances = framework_opts["pillar"]["resources"]["esxi"]["instances"]
    inject_resource_dunders(ex, "esxi-01", KEY, instances)
    esxi_authed.add(
        responses.GET,
        "https://esxi.test/api/esx/host",
        json={"version": "8.0.3", "build": "1234", "vendor": "Dell"},
        status=200,
    )
    g = ex.grains()
    assert g["resource_id"] == "esxi-01"
    assert g["resource_type"] == "esxi"
    assert g["version"] == "8.0.3"
    assert g["vendor"] == "Dell"
