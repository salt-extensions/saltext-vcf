"""Framework-interface tests for resources.sddc."""

import responses

from saltext.vcf.resources import sddc as sm

KEY = sm.CONTEXT_KEY


def test_discover(framework_opts):
    assert sm.discover(framework_opts) == ["sddc-01"]


def test_init_initialized_shutdown(monkeypatch, framework_opts):
    ctx = {}
    monkeypatch.setattr(sm, "__context__", ctx, raising=False)
    assert sm.initialized() is False
    sm.init(framework_opts)
    assert sm.initialized() is True
    sm.shutdown(framework_opts)
    assert sm.initialized() is False


def test_ping_ok(inject_resource_dunders, framework_opts, mocked_responses):
    instances = framework_opts["pillar"]["resources"]["sddc"]["instances"]
    inject_resource_dunders(sm, "sddc-01", KEY, instances)
    mocked_responses.add(
        responses.POST,
        "https://sm.test/v1/tokens",
        json={"accessToken": "t"},
        status=200,
    )
    assert sm.ping() is True


def test_host_list(inject_resource_dunders, framework_opts, sddc_authed):
    instances = framework_opts["pillar"]["resources"]["sddc"]["instances"]
    inject_resource_dunders(sm, "sddc-01", KEY, instances)
    sddc_authed.add(responses.GET, "https://sm.test/v1/hosts", json={"elements": []}, status=200)
    assert sm.host_list() == {"elements": []}


def test_credentials_rotate(inject_resource_dunders, framework_opts, sddc_authed):
    instances = framework_opts["pillar"]["resources"]["sddc"]["instances"]
    inject_resource_dunders(sm, "sddc-01", KEY, instances)
    sddc_authed.add(
        responses.PATCH,
        "https://sm.test/v1/credentials",
        json={"id": "task-1"},
        status=202,
    )
    assert sm.credentials_rotate([{"resourceName": "esxi01"}]) == {"id": "task-1"}


def test_vcf_services_routed(inject_resource_dunders, framework_opts, sddc_authed):
    instances = framework_opts["pillar"]["resources"]["sddc"]["instances"]
    inject_resource_dunders(sm, "sddc-01", KEY, instances)
    sample = {"elements": [{"id": "u1", "name": "COMMON_SERVICES", "status": "UP"}]}
    sddc_authed.add(responses.GET, "https://sm.test/v1/vcf-services", json=sample, status=200)
    sddc_authed.add(
        responses.GET,
        "https://sm.test/v1/vcf-services/u1",
        json=sample["elements"][0],
        status=200,
    )
    assert sm.vcf_services_list() == sample
    assert sm.vcf_services_get("u1")["name"] == "COMMON_SERVICES"
    assert sm.vcf_services_get_by_name("COMMON_SERVICES")["id"] == "u1"
