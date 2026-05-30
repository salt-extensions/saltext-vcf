"""
``vcf_ops`` resource type — one VCF Operations instance per resource ID.

Configuration::

    resources:
      vcf_ops:
        instances:
          ops-prod:
            host: ops.example.test
            username: admin
            password: secret
            auth_source: LOCAL          # optional
            verify_ssl: false
"""

import logging

import requests
import urllib3

from saltext.vcf.clients import vcfops_adapter
from saltext.vcf.clients import vcfops_alert
from saltext.vcf.clients import vcfops_auth
from saltext.vcf.clients import vcfops_collector
from saltext.vcf.clients import vcfops_credential
from saltext.vcf.clients import vcfops_deployment
from saltext.vcf.clients import vcfops_maintenance
from saltext.vcf.clients import vcfops_policy
from saltext.vcf.clients import vcfops_recommendation
from saltext.vcf.clients import vcfops_report
from saltext.vcf.clients import vcfops_resource
from saltext.vcf.clients import vcfops_resource_group
from saltext.vcf.clients import vcfops_solution
from saltext.vcf.clients import vcfops_supermetric
from saltext.vcf.clients import vcfops_task
from saltext.vcf.clients import vcfops_version
from saltext.vcf.resources import pillar_resources_tree

log = logging.getLogger(__name__)

CONTEXT_KEY = "vcf_ops_resource"


def __virtual__():
    return True


def _resource_id():
    return __resource__["id"]  # pylint: disable=undefined-variable


def _instance_cfg(resource_id):
    return __context__[CONTEXT_KEY]["instances"].get(  # pylint: disable=undefined-variable
        resource_id, {}
    )


def _opts():
    return {"pillar": {"saltext.vcf": {"vcf_ops": _instance_cfg(_resource_id())}}}


def init(opts):
    instances = pillar_resources_tree(opts).get("vcf_ops", {}).get("instances", {})
    __context__[CONTEXT_KEY] = {  # pylint: disable=undefined-variable
        "initialized": True,
        "instances": instances,
    }
    log.debug("vcf_ops resource init: managing %s", list(instances))


def initialized():
    return __context__.get(CONTEXT_KEY, {}).get(  # pylint: disable=undefined-variable
        "initialized", False
    )


def discover(opts):
    return list(pillar_resources_tree(opts).get("vcf_ops", {}).get("instances", {}))


def grains():
    rid = _resource_id()
    cfg = _instance_cfg(rid)
    return {"resource_type": "vcf_ops", "resource_id": rid, "host": cfg.get("host", "")}


def grains_refresh():
    return grains()


def ping():
    """Probe the token endpoint."""
    cfg = _instance_cfg(_resource_id())
    host = cfg.get("host")
    verify = cfg.get("verify_ssl", True)
    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    try:
        resp = requests.post(
            f"https://{host}/suite-api/api/auth/token/acquire",
            json={
                "username": cfg.get("username"),
                "password": cfg.get("password"),
                "authSource": cfg.get("auth_source", "LOCAL"),
            },
            verify=verify,
            timeout=10,
        )
        return resp.status_code == 200
    except requests.RequestException as exc:
        log.warning("vcf_ops ping failed for %s: %s", host, exc)
        return False


def shutdown(opts):
    __context__.pop(CONTEXT_KEY, None)  # pylint: disable=undefined-variable


# ---------------------------------------------------------------------------
# Per-resource operations
# ---------------------------------------------------------------------------


def version():
    return vcfops_version.get(_opts())


def resource_list(page=0, page_size=1000, **filters):
    return vcfops_resource.list_(_opts(), page=page, page_size=page_size, **filters)


def resource_get(resource_id):
    return vcfops_resource.get(_opts(), resource_id)


def resource_relationships(resource_id, **filters):
    return vcfops_resource.relationships(_opts(), resource_id, **filters)


def resource_stats(resource_id, **filters):
    return vcfops_resource.stats(_opts(), resource_id, **filters)


def adapter_list():
    return vcfops_adapter.list_(_opts())


def adapter_get(kind_key):
    return vcfops_adapter.get(_opts(), kind_key)


def alert_definitions_list(page=0, page_size=1000):
    return vcfops_alert.alerts_list(_opts(), page=page, page_size=page_size)


def alert_definition_get(alert_id):
    return vcfops_alert.alerts_get(_opts(), alert_id)


def symptom_definitions_list(page=0, page_size=1000):
    return vcfops_alert.symptoms_list(_opts(), page=page, page_size=page_size)


def policy_list():
    return vcfops_policy.list_(_opts())


def policy_get(policy_id):
    return vcfops_policy.get(_opts(), policy_id)


def notification_rules_list():
    return vcfops_policy.notification_rules_list(_opts())


# Active alerts (instances vs definitions)
def active_alerts_list(page=0, page_size=1000, **filters):
    return vcfops_alert.active_list(_opts(), page=page, page_size=page_size, params=filters or None)


def active_alert_get(alert_id):
    return vcfops_alert.active_get(_opts(), alert_id)


# Auth / RBAC
def auth_sources_list():
    return vcfops_auth.sources_list(_opts())


def auth_roles_list():
    return vcfops_auth.roles_list(_opts())


def auth_role_get(role_name):
    return vcfops_auth.roles_get(_opts(), role_name)


def auth_users_list():
    return vcfops_auth.users_list(_opts())


def auth_usergroups_list():
    return vcfops_auth.usergroups_list(_opts())


def auth_privileges_list():
    return vcfops_auth.privileges_list(_opts())


# Collectors
def collector_list():
    return vcfops_collector.list_(_opts())


def collector_get(collector_id):
    return vcfops_collector.get(_opts(), collector_id)


def collector_groups_list():
    return vcfops_collector.groups_list(_opts())


# Credentials
def credential_list():
    return vcfops_credential.list_(_opts())


def credential_kinds_list():
    return vcfops_credential.kinds_list(_opts())


# Solutions / management packs
def solution_list():
    return vcfops_solution.list_(_opts())


# Recommendations
def recommendation_list(page=0, page_size=1000):
    return vcfops_recommendation.list_(_opts(), page=page, page_size=page_size)


# Resource groups, super metrics, reports, maintenance, tasks, applications
def resource_group_list():
    return vcfops_resource_group.list_(_opts())


def supermetric_list(page=0, page_size=1000):
    return vcfops_supermetric.list_(_opts(), page=page, page_size=page_size)


def report_list(page=0, page_size=1000):
    return vcfops_report.list_(_opts(), page=page, page_size=page_size)


def maintenance_list(page=0, page_size=1000):
    return vcfops_maintenance.list_(_opts(), page=page, page_size=page_size)


def task_list(page=0, page_size=1000):
    return vcfops_task.list_(_opts(), page=page, page_size=page_size)


def node_status():
    return vcfops_deployment.node_status(_opts())


def application_list(page=0, page_size=1000):
    return vcfops_deployment.applications_list(_opts(), page=page, page_size=page_size)
