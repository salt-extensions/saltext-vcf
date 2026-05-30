"""
``sddc`` resource type — one SDDC Manager per resource ID.

Configuration shape::

    resources:
      sddc:
        instances:
          sddc-01:
            host: sddc-manager.example.test
            username: administrator@vsphere.local
            password: secret
            verify_ssl: false
"""

import logging

import requests
import urllib3

from saltext.vcf.clients import sddc_cluster
from saltext.vcf.clients import sddc_credentials
from saltext.vcf.clients import sddc_domain
from saltext.vcf.clients import sddc_host
from saltext.vcf.clients import sddc_vcf_services
from saltext.vcf.resources import pillar_resources_tree

log = logging.getLogger(__name__)

CONTEXT_KEY = "sddc_resource"


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
        "pillar": {"saltext.vcf": {"sddc_manager": _instance_cfg(_resource_id())}},
    }


def init(opts):
    instances = pillar_resources_tree(opts).get("sddc", {}).get("instances", {})
    __context__[CONTEXT_KEY] = {  # pylint: disable=undefined-variable
        "initialized": True,
        "instances": instances,
    }
    log.debug("sddc resource init: managing %s", list(instances))


def initialized():
    return __context__.get(CONTEXT_KEY, {}).get(  # pylint: disable=undefined-variable
        "initialized", False
    )


def discover(opts):
    return list(pillar_resources_tree(opts).get("sddc", {}).get("instances", {}))


def grains():
    rid = _resource_id()
    cfg = _instance_cfg(rid)
    return {
        "resource_type": "sddc",
        "resource_id": rid,
        "host": cfg.get("host", ""),
    }


def grains_refresh():
    return grains()


def ping():
    """Probe ``/v1/tokens`` to confirm SDDC Manager is reachable."""
    cfg = _instance_cfg(_resource_id())
    host = cfg.get("host")
    verify = cfg.get("verify_ssl", True)
    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    try:
        resp = requests.post(
            f"https://{host}/v1/tokens",
            json={"username": cfg.get("username"), "password": cfg.get("password")},
            verify=verify,
            timeout=10,
        )
        return resp.status_code == 200
    except requests.RequestException as exc:
        log.warning("sddc ping failed for %s: %s", host, exc)
        return False


def shutdown(opts):
    __context__.pop(CONTEXT_KEY, None)  # pylint: disable=undefined-variable


# ---------------------------------------------------------------------------
# Per-resource operations
# ---------------------------------------------------------------------------


def host_list():
    return sddc_host.list_(_opts())


def host_get(host):
    return sddc_host.get(_opts(), host)


def host_commission(host_specs):
    return sddc_host.commission(_opts(), host_specs)


def host_decommission(host):
    return sddc_host.decommission(_opts(), host)


def cluster_list():
    return sddc_cluster.list_(_opts())


def cluster_get(cluster):
    return sddc_cluster.get(_opts(), cluster)


def cluster_create(cluster_spec):
    return sddc_cluster.create(_opts(), cluster_spec)


def cluster_delete(cluster):
    return sddc_cluster.delete(_opts(), cluster)


def domain_list():
    return sddc_domain.list_(_opts())


def domain_get(domain):
    return sddc_domain.get(_opts(), domain)


def credentials_list():
    return sddc_credentials.list_(_opts())


def credentials_rotate(elements):
    return sddc_credentials.rotate(_opts(), elements)


# VMSP platform services (mediated via /v1/vcf-services)
def vcf_services_list():
    return sddc_vcf_services.list_(_opts())


def vcf_services_get(service_id):
    return sddc_vcf_services.get(_opts(), service_id)


def vcf_services_get_by_name(name):
    return sddc_vcf_services.get_by_name(_opts(), name)
