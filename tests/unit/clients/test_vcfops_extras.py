"""Tests for the expanded VCF Operations clients (auth/collector/credential/recommendation/etc.)."""

import responses

from saltext.vcf.clients import vcfops_alert
from saltext.vcf.clients import vcfops_auth
from saltext.vcf.clients import vcfops_collector
from saltext.vcf.clients import vcfops_credential
from saltext.vcf.clients import vcfops_deployment
from saltext.vcf.clients import vcfops_maintenance
from saltext.vcf.clients import vcfops_recommendation
from saltext.vcf.clients import vcfops_report
from saltext.vcf.clients import vcfops_resource_group
from saltext.vcf.clients import vcfops_solution
from saltext.vcf.clients import vcfops_supermetric
from saltext.vcf.clients import vcfops_task

OPS = "https://ops.test/suite-api/api"


def test_auth_sources_roles_privileges_users(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, f"{OPS}/auth/sources", json={"sources": []}, status=200)
    vcfops_authed.add(
        responses.GET,
        f"{OPS}/auth/roles",
        json={"userRoles": [{"name": "Admin"}]},
        status=200,
    )
    vcfops_authed.add(responses.GET, f"{OPS}/auth/roles/Admin", json={"name": "Admin"}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/auth/roles/missing", status=404)
    vcfops_authed.add(responses.POST, f"{OPS}/auth/roles", json={}, status=200)
    vcfops_authed.add(responses.DELETE, f"{OPS}/auth/roles/MyRole", status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/auth/privileges", json={"privileges": []}, status=200)
    vcfops_authed.add(
        responses.GET, f"{OPS}/auth/users", json={"users": [{"id": "u-1"}]}, status=200
    )
    vcfops_authed.add(responses.GET, f"{OPS}/auth/users/u-1", json={"id": "u-1"}, status=200)
    vcfops_authed.add(responses.POST, f"{OPS}/auth/users", json={}, status=200)
    vcfops_authed.add(responses.PUT, f"{OPS}/auth/users/u-1", json={}, status=200)
    vcfops_authed.add(responses.DELETE, f"{OPS}/auth/users/u-1", status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/auth/usergroups", json={"userGroups": []}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/auth/usergroups/g-1", json={"id": "g-1"}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/auth/usergroups/missing", status=404)
    vcfops_authed.add(responses.POST, f"{OPS}/auth/usergroups", json={}, status=200)
    vcfops_authed.add(responses.DELETE, f"{OPS}/auth/usergroups/g-1", status=200)

    assert vcfops_auth.sources_list(opts) == {"sources": []}
    assert vcfops_auth.roles_list(opts)["userRoles"][0]["name"] == "Admin"
    assert vcfops_auth.roles_get(opts, "Admin")["name"] == "Admin"
    assert vcfops_auth.roles_get_or_none(opts, "missing") is None
    vcfops_auth.roles_create(opts, {"name": "MyRole"})
    vcfops_auth.roles_delete(opts, "MyRole")
    assert vcfops_auth.privileges_list(opts) == {"privileges": []}
    assert vcfops_auth.users_list(opts)["users"][0]["id"] == "u-1"
    assert vcfops_auth.users_get(opts, "u-1") == {"id": "u-1"}
    vcfops_auth.users_create(opts, {"username": "x"})
    vcfops_auth.users_update(opts, "u-1", {"firstName": "y"})
    vcfops_auth.users_delete(opts, "u-1")
    assert vcfops_auth.usergroups_list(opts) == {"userGroups": []}
    assert vcfops_auth.usergroups_get(opts, "g-1") == {"id": "g-1"}
    assert vcfops_auth.usergroups_get_or_none(opts, "missing") is None
    vcfops_auth.usergroups_create(opts, {"name": "g"})
    vcfops_auth.usergroups_delete(opts, "g-1")


def test_collector_and_groups(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, f"{OPS}/collectors", json={"collector": []}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/collectors/1", json={"id": 1}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/collectors/missing", status=404)
    vcfops_authed.add(responses.DELETE, f"{OPS}/collectors/1", status=200)
    vcfops_authed.add(
        responses.GET,
        f"{OPS}/collectorgroups",
        json={"collectorGroups": []},
        status=200,
    )
    vcfops_authed.add(responses.GET, f"{OPS}/collectorgroups/g", json={"id": "g"}, status=200)
    vcfops_authed.add(responses.POST, f"{OPS}/collectorgroups", json={}, status=200)
    vcfops_authed.add(responses.PUT, f"{OPS}/collectorgroups/g", json={}, status=200)
    vcfops_authed.add(responses.DELETE, f"{OPS}/collectorgroups/g", status=200)
    assert vcfops_collector.list_(opts) == {"collector": []}
    assert vcfops_collector.get(opts, "1") == {"id": 1}
    assert vcfops_collector.get_or_none(opts, "missing") is None
    vcfops_collector.delete(opts, "1")
    assert vcfops_collector.groups_list(opts) == {"collectorGroups": []}
    assert vcfops_collector.groups_get(opts, "g")["id"] == "g"
    vcfops_collector.groups_create(opts, {})
    vcfops_collector.groups_update(opts, "g", {})
    vcfops_collector.groups_delete(opts, "g")


def test_credential(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        f"{OPS}/credentials",
        json={"credentialInstances": []},
        status=200,
    )
    vcfops_authed.add(responses.GET, f"{OPS}/credentials/c", json={"id": "c"}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/credentials/missing", status=404)
    vcfops_authed.add(responses.POST, f"{OPS}/credentials", json={}, status=200)
    vcfops_authed.add(responses.PUT, f"{OPS}/credentials/c", json={}, status=200)
    vcfops_authed.add(responses.DELETE, f"{OPS}/credentials/c", status=200)
    vcfops_authed.add(
        responses.GET,
        f"{OPS}/credentialkinds",
        json={"credentialTypes": []},
        status=200,
    )
    assert vcfops_credential.list_(opts) == {"credentialInstances": []}
    assert vcfops_credential.get(opts, "c")["id"] == "c"
    assert vcfops_credential.get_or_none(opts, "missing") is None
    vcfops_credential.create(opts, {})
    vcfops_credential.update(opts, "c", {})
    vcfops_credential.delete(opts, "c")
    assert vcfops_credential.kinds_list(opts) == {"credentialTypes": []}


def test_alert_active_endpoints(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, f"{OPS}/alerts", json={"alerts": []}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/alerts/a", json={"alertId": "a"}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/alerts/missing", status=404)
    vcfops_authed.add(responses.GET, f"{OPS}/symptomdefinitions/s", json={"id": "s"}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/symptomdefinitions/missing", status=404)
    assert vcfops_alert.active_list(opts) == {"alerts": []}
    assert vcfops_alert.active_get(opts, "a")["alertId"] == "a"
    assert vcfops_alert.active_get_or_none(opts, "missing") is None
    assert vcfops_alert.symptoms_get(opts, "s")["id"] == "s"
    assert vcfops_alert.symptoms_get_or_none(opts, "missing") is None


def test_alert_active_with_filters(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, f"{OPS}/alerts", json={"alerts": []}, status=200)
    vcfops_alert.active_list(opts, params={"activeOnly": True, "resourceId": "uuid"})
    call = vcfops_authed.calls[-1]
    assert "activeOnly=True" in call.request.url
    assert "resourceId=uuid" in call.request.url


def test_recommendation_list_get_or_none(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        f"{OPS}/recommendations",
        json={"recommendations": []},
        status=200,
    )
    vcfops_authed.add(responses.GET, f"{OPS}/recommendations/r", json={"id": "r"}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/recommendations/missing", status=404)
    assert vcfops_recommendation.list_(opts) == {"recommendations": []}
    assert vcfops_recommendation.get(opts, "r")["id"] == "r"
    assert vcfops_recommendation.get_or_none(opts, "missing") is None


def test_resource_group(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, f"{OPS}/resources/groups", json={"groups": []}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/resources/groups/g", json={"id": "g"}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/resources/groups/missing", status=404)
    vcfops_authed.add(responses.POST, f"{OPS}/resources/groups", json={}, status=200)
    vcfops_authed.add(responses.PUT, f"{OPS}/resources/groups/g", json={}, status=200)
    vcfops_authed.add(responses.DELETE, f"{OPS}/resources/groups/g", status=200)
    assert vcfops_resource_group.list_(opts) == {"groups": []}
    assert vcfops_resource_group.get(opts, "g")["id"] == "g"
    assert vcfops_resource_group.get_or_none(opts, "missing") is None
    vcfops_resource_group.create(opts, {})
    vcfops_resource_group.update(opts, "g", {})
    vcfops_resource_group.delete(opts, "g")


def test_supermetric(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, f"{OPS}/supermetrics", json={"superMetrics": []}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/supermetrics/s", json={"id": "s"}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/supermetrics/missing", status=404)
    vcfops_authed.add(responses.POST, f"{OPS}/supermetrics", json={}, status=200)
    vcfops_authed.add(responses.PUT, f"{OPS}/supermetrics/s", json={}, status=200)
    vcfops_authed.add(responses.DELETE, f"{OPS}/supermetrics/s", status=200)
    assert vcfops_supermetric.list_(opts) == {"superMetrics": []}
    assert vcfops_supermetric.get(opts, "s")["id"] == "s"
    assert vcfops_supermetric.get_or_none(opts, "missing") is None
    vcfops_supermetric.create(opts, {})
    vcfops_supermetric.update(opts, "s", {})
    vcfops_supermetric.delete(opts, "s")


def test_report(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, f"{OPS}/reports", json={"reports": []}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/reports/r", json={"id": "r"}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/reports/missing", status=404)
    vcfops_authed.add(responses.POST, f"{OPS}/reports", json={"id": "new"}, status=200)
    vcfops_authed.add(responses.DELETE, f"{OPS}/reports/r", status=200)
    vcfops_authed.add(
        responses.GET, f"{OPS}/reports/r/download", body=b"binary-pdf-bytes", status=200
    )
    assert vcfops_report.list_(opts) == {"reports": []}
    assert vcfops_report.get(opts, "r")["id"] == "r"
    assert vcfops_report.get_or_none(opts, "missing") is None
    assert vcfops_report.generate(opts, {})["id"] == "new"
    assert vcfops_report.download(opts, "r") == b"binary-pdf-bytes"
    vcfops_report.delete(opts, "r")


def test_maintenance(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET, f"{OPS}/maintenanceschedules", json={"schedules": []}, status=200
    )
    vcfops_authed.add(responses.GET, f"{OPS}/maintenanceschedules/m", json={"id": "m"}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/maintenanceschedules/missing", status=404)
    vcfops_authed.add(responses.POST, f"{OPS}/maintenanceschedules", json={}, status=200)
    vcfops_authed.add(responses.PUT, f"{OPS}/maintenanceschedules/m", json={}, status=200)
    vcfops_authed.add(responses.DELETE, f"{OPS}/maintenanceschedules/m", status=200)
    assert vcfops_maintenance.list_(opts) == {"schedules": []}
    assert vcfops_maintenance.get(opts, "m")["id"] == "m"
    assert vcfops_maintenance.get_or_none(opts, "missing") is None
    vcfops_maintenance.create(opts, {})
    vcfops_maintenance.update(opts, "m", {})
    vcfops_maintenance.delete(opts, "m")


def test_task(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, f"{OPS}/tasks", json={"taskStatusList": []}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/tasks/t", json={"id": "t"}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/tasks/missing", status=404)
    assert vcfops_task.list_(opts) == {"taskStatusList": []}
    assert vcfops_task.get(opts, "t")["id"] == "t"
    assert vcfops_task.get_or_none(opts, "missing") is None


def test_solution(opts, vcfops_authed):
    vcfops_authed.add(responses.GET, f"{OPS}/solutions", json={"solution": []}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/solutions/s", json={"id": "s"}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/solutions/missing", status=404)
    assert vcfops_solution.list_(opts) == {"solution": []}
    assert vcfops_solution.get(opts, "s")["id"] == "s"
    assert vcfops_solution.get_or_none(opts, "missing") is None


def test_deployment_node_status_and_applications(opts, vcfops_authed):
    vcfops_authed.add(
        responses.GET,
        f"{OPS}/deployment/node/status",
        json={"status": "ONLINE", "systemTime": 1},
        status=200,
    )
    vcfops_authed.add(
        responses.GET,
        f"{OPS}/applications",
        json={"appMonitoringConfigurations": []},
        status=200,
    )
    vcfops_authed.add(responses.GET, f"{OPS}/applications/a", json={"id": "a"}, status=200)
    vcfops_authed.add(responses.GET, f"{OPS}/applications/missing", status=404)
    assert vcfops_deployment.node_status(opts)["status"] == "ONLINE"
    assert vcfops_deployment.applications_list(opts) == {"appMonitoringConfigurations": []}
    assert vcfops_deployment.applications_get(opts, "a")["id"] == "a"
    assert vcfops_deployment.applications_get_or_none(opts, "missing") is None
