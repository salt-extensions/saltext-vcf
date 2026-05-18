"""Framework-interface tests for resources.nsx."""

import responses

from saltext.vcf.resources import nsx as nx

KEY = nx.CONTEXT_KEY


def test_discover(framework_opts):
    assert nx.discover(framework_opts) == ["mgmt-nsx"]


def test_init_initialized_shutdown(monkeypatch, framework_opts):
    ctx = {}
    monkeypatch.setattr(nx, "__context__", ctx, raising=False)
    nx.init(framework_opts)
    assert nx.initialized() is True
    nx.shutdown(framework_opts)
    assert nx.initialized() is False


def test_ping_ok(inject_resource_dunders, framework_opts, mocked_responses):
    instances = framework_opts["pillar"]["resources"]["nsx"]["instances"]
    inject_resource_dunders(nx, "mgmt-nsx", KEY, instances)
    mocked_responses.add(responses.GET, "https://nsx.test/policy/api/v1/infra", json={}, status=200)
    assert nx.ping() is True


def test_segment_create_put(inject_resource_dunders, framework_opts, mocked_responses):
    instances = framework_opts["pillar"]["resources"]["nsx"]["instances"]
    inject_resource_dunders(nx, "mgmt-nsx", KEY, instances)
    mocked_responses.add(
        responses.PUT,
        "https://nsx.test/policy/api/v1/infra/segments/seg-a",
        json={"id": "seg-a"},
        status=200,
    )
    assert nx.segment_create("seg-a", transport_zone_path="/tz/1") == {"id": "seg-a"}


def test_group_delete(inject_resource_dunders, framework_opts, mocked_responses):
    instances = framework_opts["pillar"]["resources"]["nsx"]["instances"]
    inject_resource_dunders(nx, "mgmt-nsx", KEY, instances)
    mocked_responses.add(
        responses.DELETE,
        "https://nsx.test/policy/api/v1/infra/domains/default/groups/g-a",
        status=200,
    )
    assert nx.group_delete("g-a") == {}
