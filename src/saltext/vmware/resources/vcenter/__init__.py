"""
``vcenter`` resource type — exposes one or more vCenter instances as Salt
Resources.

Each ``vcenter`` resource maps to one vCenter Server, identified by an
instance ID under ``resources.vcenter.instances`` in the configured pillar
subtree::

    resources:
      vcenter:
        instances:
          mgmt-vc:
            host: mgmt-vc.vcf.nimbus.internal
            username: administrator@vsphere.local
            password: VMware123!VMware123!
            verify_ssl: false

The current resource is conveyed by the loader via ``__resource__["id"]``;
per-resource functions never accept a resource id as a parameter. All REST
work is delegated to :mod:`saltext.vmware.clients` so that the standalone
execution modules and the Resources framework share one implementation.
"""

import logging

import requests
import urllib3

from saltext.vmware.clients import vcenter_appliance
from saltext.vmware.clients import vcenter_cluster
from saltext.vmware.clients import vcenter_datacenter
from saltext.vmware.clients import vcenter_datastore
from saltext.vmware.clients import vcenter_host
from saltext.vmware.clients import vcenter_network
from saltext.vmware.clients import vcenter_storage_policy
from saltext.vmware.clients import vcenter_supervisor
from saltext.vmware.clients import vcenter_supervisor_compat
from saltext.vmware.clients import vcenter_supervisor_service
from saltext.vmware.clients import vcenter_supervisor_software
from saltext.vmware.clients import vcenter_tag
from saltext.vmware.clients import vcenter_vm
from saltext.vmware.clients import vcenter_vm_class
from saltext.vmware.resources import pillar_resources_tree

log = logging.getLogger(__name__)

CONTEXT_KEY = "vcenter_resource"


def __virtual__():
    return True


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resource_id():
    return __resource__["id"]  # pylint: disable=undefined-variable


def _instance_cfg(resource_id):
    return __context__[CONTEXT_KEY]["instances"].get(  # pylint: disable=undefined-variable
        resource_id, {}
    )


def _opts_for(resource_id):
    """Build a clients/-compatible opts dict for the named instance."""
    return {
        "pillar": {"saltext.vmware": {"vcenter": _instance_cfg(resource_id)}},
    }


def _opts():
    return _opts_for(_resource_id())


# ---------------------------------------------------------------------------
# Framework interface
# ---------------------------------------------------------------------------


def init(opts):
    """Load instance configs from pillar and cache them in ``__context__``."""
    cfg = pillar_resources_tree(opts).get("vcenter", {})
    instances = cfg.get("instances", {})
    __context__[CONTEXT_KEY] = {  # pylint: disable=undefined-variable
        "initialized": True,
        "instances": instances,
    }
    log.debug("vcenter resource init: managing %s", list(instances))


def initialized():
    return __context__.get(CONTEXT_KEY, {}).get(  # pylint: disable=undefined-variable
        "initialized", False
    )


def discover(opts):
    """Return the list of vCenter instance IDs this minion manages."""
    instances = pillar_resources_tree(opts).get("vcenter", {}).get("instances", {})
    return list(instances)


def grains():
    """Return basic identity grains for the current vCenter instance."""
    rid = _resource_id()
    cfg = _instance_cfg(rid)
    return {
        "resource_type": "vcenter",
        "resource_id": rid,
        "host": cfg.get("host", ""),
    }


def grains_refresh():
    return grains()


def ping():
    """Probe ``/api/session`` to confirm the current vCenter is reachable."""
    cfg = _instance_cfg(_resource_id())
    host = cfg.get("host")
    verify = cfg.get("verify_ssl", True)
    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    try:
        resp = requests.post(
            f"https://{host}/api/session",
            auth=(cfg.get("username"), cfg.get("password")),
            verify=verify,
            timeout=10,
        )
        return resp.status_code in (200, 201)
    except requests.RequestException as exc:
        log.warning("vcenter ping failed for %s: %s", host, exc)
        return False


def shutdown(opts):
    __context__.pop(CONTEXT_KEY, None)  # pylint: disable=undefined-variable


# ---------------------------------------------------------------------------
# Per-resource operations (delegated to clients/)
# ---------------------------------------------------------------------------


def cluster_list():
    return vcenter_cluster.list_(_opts())


def cluster_get(cluster):
    return vcenter_cluster.get(_opts(), cluster)


def cluster_create(name, datacenter=None, **spec):
    return vcenter_cluster.create(_opts(), name, datacenter=datacenter, **spec)


def cluster_delete(cluster):
    return vcenter_cluster.delete(_opts(), cluster)


def host_list():
    return vcenter_host.list_(_opts())


def host_get(host):
    return vcenter_host.get(_opts(), host)


def host_enter_maintenance(host):
    return vcenter_host.enter_maintenance(_opts(), host)


def host_exit_maintenance(host):
    return vcenter_host.exit_maintenance(_opts(), host)


def vm_list():
    return vcenter_vm.list_(_opts())


def vm_get(vm):
    return vcenter_vm.get(_opts(), vm)


def vm_power_on(vm):
    return vcenter_vm.power_on(_opts(), vm)


def vm_power_off(vm):
    return vcenter_vm.power_off(_opts(), vm)


def vm_reset(vm):
    return vcenter_vm.reset(_opts(), vm)


def datacenter_list():
    return vcenter_datacenter.list_(_opts())


def datacenter_get(datacenter):
    return vcenter_datacenter.get(_opts(), datacenter)


def datacenter_create(name, folder=None):
    return vcenter_datacenter.create(_opts(), name, folder=folder)


def datacenter_delete(datacenter):
    return vcenter_datacenter.delete(_opts(), datacenter)


def tag_list():
    return vcenter_tag.list_(_opts())


def tag_create(name, category_id, description=""):
    return vcenter_tag.create(_opts(), name, category_id, description=description)


def tag_delete(tag):
    return vcenter_tag.delete(_opts(), tag)


def tag_assign(tag, object_type, object_id):
    return vcenter_tag.assign(_opts(), tag, object_type, object_id)


def tag_list_assigned(object_type, object_id):
    return vcenter_tag.list_assigned(_opts(), object_type, object_id)


# Datastores
def datastore_list():
    return vcenter_datastore.list_(_opts())


def datastore_get(datastore):
    return vcenter_datastore.get(_opts(), datastore)


# Networks
def network_list():
    return vcenter_network.list_(_opts())


# Storage policies
def storage_policy_list():
    return vcenter_storage_policy.list_(_opts())


def storage_policy_get(policy):
    return vcenter_storage_policy.get(_opts(), policy)


# Appliance
def appliance_services_list():
    return vcenter_appliance.services_list(_opts())


def appliance_services_get(service):
    return vcenter_appliance.services_get(_opts(), service)


def appliance_services_start(service):
    return vcenter_appliance.services_start(_opts(), service)


def appliance_services_stop(service):
    return vcenter_appliance.services_stop(_opts(), service)


def appliance_services_restart(service):
    return vcenter_appliance.services_restart(_opts(), service)


def appliance_version():
    return vcenter_appliance.version(_opts())


def appliance_health_system():
    return vcenter_appliance.health_system(_opts())


def appliance_dns_get():
    return vcenter_appliance.dns_get(_opts())


def appliance_dns_set(servers, mode="is_static"):
    return vcenter_appliance.dns_set(_opts(), servers, mode=mode)


def appliance_logging_forwarding_get():
    return vcenter_appliance.logging_forwarding_get(_opts())


def appliance_logging_forwarding_set(servers):
    return vcenter_appliance.logging_forwarding_set(_opts(), servers)


# VKS / Supervisor
def supervisor_cluster_list():
    return vcenter_supervisor.list_clusters(_opts())


def supervisor_cluster_get(cluster):
    return vcenter_supervisor.get_cluster(_opts(), cluster)


def supervisor_compatibility_list():
    return vcenter_supervisor.list_compatibility(_opts())


def supervisor_namespace_list():
    return vcenter_supervisor.list_namespaces(_opts())


def supervisor_namespace_get(namespace):
    return vcenter_supervisor.get_namespace(_opts(), namespace)


def supervisor_service_list():
    return vcenter_supervisor_service.list_(_opts())


def supervisor_service_get(service):
    return vcenter_supervisor_service.get(_opts(), service)


def supervisor_service_versions(service):
    return vcenter_supervisor_service.list_versions(_opts(), service)


def vm_class_list():
    return vcenter_vm_class.list_(_opts())


def vm_class_get(vm_class):
    return vcenter_vm_class.get(_opts(), vm_class)


def supervisor_software_list():
    return vcenter_supervisor_software.list_(_opts())


def supervisor_software_get(cluster):
    return vcenter_supervisor_software.get(_opts(), cluster)


def supervisor_size_info():
    return vcenter_supervisor_compat.get_cluster_size_info(_opts())


def supervisor_dvs_compatibility(cluster):
    return vcenter_supervisor_compat.list_dvs_compatibility(_opts(), cluster)
