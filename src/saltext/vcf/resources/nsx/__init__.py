"""
``nsx`` resource type — one NSX Manager per resource ID.

Configuration shape::

    resources:
      nsx:
        instances:
          mgmt-nsx:
            host: mgmt-nsx.vcf.nimbus.internal
            username: admin
            password: VMware123!VMware123!
            verify_ssl: false
"""

import logging

import requests
import urllib3

from saltext.vcf.clients import nsx_cluster
from saltext.vcf.clients import nsx_compute_collection
from saltext.vcf.clients import nsx_context_profile
from saltext.vcf.clients import nsx_firewall_rule
from saltext.vcf.clients import nsx_group
from saltext.vcf.clients import nsx_node
from saltext.vcf.clients import nsx_role_binding
from saltext.vcf.clients import nsx_security_policy
from saltext.vcf.clients import nsx_segment
from saltext.vcf.clients import nsx_service
from saltext.vcf.clients import nsx_tier0
from saltext.vcf.clients import nsx_tier1
from saltext.vcf.clients import nsx_transport_node
from saltext.vcf.clients import nsx_transport_zone
from saltext.vcf.resources import pillar_resources_tree

log = logging.getLogger(__name__)

CONTEXT_KEY = "nsx_resource"


def __virtual__():
    return True


def _resource_id():
    return __resource__["id"]  # pylint: disable=undefined-variable


def _instance_cfg(resource_id):
    return __context__[CONTEXT_KEY]["instances"].get(  # pylint: disable=undefined-variable
        resource_id, {}
    )


def _opts():
    return {
        "pillar": {"saltext.vcf": {"nsx": _instance_cfg(_resource_id())}},
    }


def init(opts):
    instances = pillar_resources_tree(opts).get("nsx", {}).get("instances", {})
    __context__[CONTEXT_KEY] = {  # pylint: disable=undefined-variable
        "initialized": True,
        "instances": instances,
    }
    log.debug("nsx resource init: managing %s", list(instances))


def initialized():
    return __context__.get(CONTEXT_KEY, {}).get(  # pylint: disable=undefined-variable
        "initialized", False
    )


def discover(opts):
    return list(pillar_resources_tree(opts).get("nsx", {}).get("instances", {}))


def grains():
    rid = _resource_id()
    cfg = _instance_cfg(rid)
    return {
        "resource_type": "nsx",
        "resource_id": rid,
        "host": cfg.get("host", ""),
    }


def grains_refresh():
    return grains()


def ping():
    """Probe ``/policy/api/v1/infra`` to confirm NSX Manager is reachable."""
    cfg = _instance_cfg(_resource_id())
    host = cfg.get("host")
    verify = cfg.get("verify_ssl", True)
    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    try:
        resp = requests.get(
            f"https://{host}/policy/api/v1/infra",
            auth=(cfg.get("username"), cfg.get("password")),
            verify=verify,
            timeout=10,
        )
        return resp.status_code == 200
    except requests.RequestException as exc:
        log.warning("nsx ping failed for %s: %s", host, exc)
        return False


def shutdown(opts):
    __context__.pop(CONTEXT_KEY, None)  # pylint: disable=undefined-variable


# ---------------------------------------------------------------------------
# Per-resource operations
# ---------------------------------------------------------------------------


def segment_list():
    return nsx_segment.list_(_opts())


def segment_get(segment):
    return nsx_segment.get(_opts(), segment)


def segment_create(segment, **spec):
    return nsx_segment.create(_opts(), segment, **spec)


def segment_delete(segment):
    return nsx_segment.delete(_opts(), segment)


def tier0_list():
    return nsx_tier0.list_(_opts())


def tier0_get(tier0):
    return nsx_tier0.get(_opts(), tier0)


def tier1_list():
    return nsx_tier1.list_(_opts())


def tier1_get(tier1):
    return nsx_tier1.get(_opts(), tier1)


def tier1_create(tier1, **spec):
    return nsx_tier1.create(_opts(), tier1, **spec)


def tier1_delete(tier1):
    return nsx_tier1.delete(_opts(), tier1)


def group_list():
    return nsx_group.list_(_opts())


def group_get(group):
    return nsx_group.get(_opts(), group)


def group_create(group, **spec):
    return nsx_group.create(_opts(), group, **spec)


def group_delete(group):
    return nsx_group.delete(_opts(), group)


# Security policies
def security_policy_list(domain="default"):
    return nsx_security_policy.list_(_opts(), domain=domain)


def security_policy_get(policy, domain="default"):
    return nsx_security_policy.get(_opts(), policy, domain=domain)


def security_policy_create(policy, domain="default", **spec):
    return nsx_security_policy.create(_opts(), policy, domain=domain, **spec)


def security_policy_delete(policy, domain="default"):
    return nsx_security_policy.delete(_opts(), policy, domain=domain)


# Firewall rules
def firewall_rule_list(policy, domain="default"):
    return nsx_firewall_rule.list_(_opts(), policy, domain=domain)


def firewall_rule_get(rule, policy, domain="default"):
    return nsx_firewall_rule.get(_opts(), rule, policy, domain=domain)


def firewall_rule_create(rule, policy, domain="default", **spec):
    return nsx_firewall_rule.create(_opts(), rule, policy, domain=domain, **spec)


def firewall_rule_delete(rule, policy, domain="default"):
    return nsx_firewall_rule.delete(_opts(), rule, policy, domain=domain)


# Services
def service_list():
    return nsx_service.list_(_opts())


def service_get(service):
    return nsx_service.get(_opts(), service)


def service_create(service, **spec):
    return nsx_service.create(_opts(), service, **spec)


def service_delete(service):
    return nsx_service.delete(_opts(), service)


# Context profiles
def context_profile_list():
    return nsx_context_profile.list_(_opts())


def context_profile_get(profile_id):
    return nsx_context_profile.get(_opts(), profile_id)


def context_profile_create(profile_id, **spec):
    return nsx_context_profile.create(_opts(), profile_id, **spec)


def context_profile_delete(profile_id):
    return nsx_context_profile.delete(_opts(), profile_id)


# Management API
def node_info():
    return nsx_node.get(_opts())


def cluster_status():
    return nsx_cluster.status(_opts())


def transport_zone_list():
    return nsx_transport_zone.list_(_opts())


def transport_zone_get(zone_id):
    return nsx_transport_zone.get(_opts(), zone_id)


def transport_node_list():
    return nsx_transport_node.list_(_opts())


def transport_node_get(node_id):
    return nsx_transport_node.get(_opts(), node_id)


def compute_collection_list():
    return nsx_compute_collection.list_(_opts())


def compute_collection_get(collection_id):
    return nsx_compute_collection.get(_opts(), collection_id)


def role_binding_list():
    return nsx_role_binding.list_(_opts())


def role_binding_get(binding_id):
    return nsx_role_binding.get(_opts(), binding_id)


def role_binding_create(name, type_, roles, **spec):
    return nsx_role_binding.create(_opts(), name, type_, roles, **spec)


def role_binding_update(binding_id, body):
    return nsx_role_binding.update(_opts(), binding_id, body)


def role_binding_delete(binding_id):
    return nsx_role_binding.delete(_opts(), binding_id)
