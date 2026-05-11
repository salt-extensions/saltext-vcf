"""Framework-interface tests for resources.vcfops."""

import responses

from saltext.vmware.resources import vcfops as op

KEY = op.CONTEXT_KEY


def test_discover(framework_opts):
    assert op.discover(framework_opts) == ["ops-prod"]


def test_init_initialized_shutdown(monkeypatch, framework_opts):
    ctx = {}
    monkeypatch.setattr(op, "__context__", ctx, raising=False)
    assert op.initialized() is False
    op.init(framework_opts)
    assert op.initialized() is True
    assert "ops-prod" in ctx[KEY]["instances"]
    op.shutdown(framework_opts)
    assert KEY not in ctx


def test_ping_ok(inject_resource_dunders, framework_opts, mocked_responses):
    instances = framework_opts["pillar"]["resources"]["vcf_ops"]["instances"]
    inject_resource_dunders(op, "ops-prod", KEY, instances)
    mocked_responses.add(
        responses.POST,
        "https://ops.test/suite-api/api/auth/token/acquire",
        json={"token": "t"},
        status=200,
    )
    assert op.ping() is True


def test_ping_unreachable(inject_resource_dunders, framework_opts, mocked_responses):
    instances = framework_opts["pillar"]["resources"]["vcf_ops"]["instances"]
    inject_resource_dunders(op, "ops-prod", KEY, instances)
    mocked_responses.add(
        responses.POST,
        "https://ops.test/suite-api/api/auth/token/acquire",
        status=401,
    )
    assert op.ping() is False


def test_version_routes(inject_resource_dunders, framework_opts, vcfops_authed):
    instances = framework_opts["pillar"]["resources"]["vcf_ops"]["instances"]
    inject_resource_dunders(op, "ops-prod", KEY, instances)
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/versions",
        json={"values": []},
        status=200,
    )
    assert op.version() == {"values": []}


def test_resource_list(inject_resource_dunders, framework_opts, vcfops_authed):
    instances = framework_opts["pillar"]["resources"]["vcf_ops"]["instances"]
    inject_resource_dunders(op, "ops-prod", KEY, instances)
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/resources",
        json={"resourceList": []},
        status=200,
    )
    assert op.resource_list(page=0, page_size=10) == {"resourceList": []}


def test_alert_definitions_list(inject_resource_dunders, framework_opts, vcfops_authed):
    instances = framework_opts["pillar"]["resources"]["vcf_ops"]["instances"]
    inject_resource_dunders(op, "ops-prod", KEY, instances)
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/alertdefinitions",
        json={"alertDefinitions": []},
        status=200,
    )
    assert op.alert_definitions_list() == {"alertDefinitions": []}


def test_extended_ops_routed(inject_resource_dunders, framework_opts, vcfops_authed):
    """A few of the new resource framework ops should hit the right URL on the right host."""
    instances = framework_opts["pillar"]["resources"]["vcf_ops"]["instances"]
    inject_resource_dunders(op, "ops-prod", KEY, instances)
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/auth/roles",
        json={"userRoles": [{"name": "Admin"}]},
        status=200,
    )
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/collectors",
        json={"collector": []},
        status=200,
    )
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/deployment/node/status",
        json={"status": "ONLINE"},
        status=200,
    )
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/alerts",
        json={"alerts": []},
        status=200,
    )
    vcfops_authed.add(
        responses.GET,
        "https://ops.test/suite-api/api/resources/groups",
        json={"groups": []},
        status=200,
    )
    assert op.auth_roles_list()["userRoles"][0]["name"] == "Admin"
    assert op.collector_list() == {"collector": []}
    assert op.node_status()["status"] == "ONLINE"
    assert op.active_alerts_list() == {"alerts": []}
    assert op.resource_group_list() == {"groups": []}
