"""
``esxi`` resource type — one **standalone** ESXi host per resource ID.

ESXi joined to a vCenter has its direct REST API locked; for those hosts
use the cluster-level :mod:`saltext.vcf.modules.vcf_cluster_config`
instead. This resource type targets ESXi hosts that respond to vAPI
session on ``POST /api/session`` directly.

Configuration::

    resources:
      esxi:
        instances:
          esxi-standalone:
            host: esxi01.example.com
            username: root
            password: VMware123!
            verify_ssl: false
"""

import logging

import requests
import urllib3

from saltext.vcf.clients import esxi_advanced
from saltext.vcf.clients import esxi_firewall
from saltext.vcf.clients import esxi_host
from saltext.vcf.clients import esxi_ntp
from saltext.vcf.clients import esxi_service
from saltext.vcf.clients import esxi_syslog
from saltext.vcf.resources import pillar_resources_tree

log = logging.getLogger(__name__)

CONTEXT_KEY = "esxi_resource"


def __virtual__():
    return True


def _resource_id():
    return __resource__["id"]  # pylint: disable=undefined-variable


def _instance_cfg(resource_id):
    return __context__[CONTEXT_KEY]["instances"].get(  # pylint: disable=undefined-variable
        resource_id, {}
    )


def _opts():
    return {"pillar": {"saltext.vcf": {"esxi": _instance_cfg(_resource_id())}}}


# ---------------------------------------------------------------------------
# Framework interface
# ---------------------------------------------------------------------------


def init(opts):
    instances = pillar_resources_tree(opts).get("esxi", {}).get("instances", {})
    __context__[CONTEXT_KEY] = {  # pylint: disable=undefined-variable
        "initialized": True,
        "instances": instances,
    }
    log.debug("esxi resource init: managing %s", list(instances))


def initialized():
    return __context__.get(CONTEXT_KEY, {}).get(  # pylint: disable=undefined-variable
        "initialized", False
    )


def discover(opts):
    return list(pillar_resources_tree(opts).get("esxi", {}).get("instances", {}))


def grains():
    rid = _resource_id()
    cfg = _instance_cfg(rid)
    g = {"resource_type": "esxi", "resource_id": rid, "host": cfg.get("host", "")}
    try:
        info = esxi_host.info(_opts())
        if isinstance(info, dict):
            for key in ("version", "build", "product_line_id", "vendor"):
                if key in info:
                    g[key] = info[key]
    except requests.RequestException as exc:
        log.warning("esxi grains: host.info call failed for %s: %s", rid, exc)
    return g


def grains_refresh():
    return grains()


def ping():
    """Probe ``/api/session`` to confirm the ESXi host is reachable."""
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
        return resp.status_code == 200
    except requests.RequestException as exc:
        log.warning("esxi ping failed for %s: %s", host, exc)
        return False


def shutdown(opts):
    __context__.pop(CONTEXT_KEY, None)  # pylint: disable=undefined-variable


# ---------------------------------------------------------------------------
# Per-resource operations
# ---------------------------------------------------------------------------


def host_info():
    return esxi_host.info(_opts())


def host_lockdown_get():
    return esxi_host.lockdown_get(_opts())


def host_lockdown_set(mode, exception_users=None):
    return esxi_host.lockdown_set(_opts(), mode, exception_users=exception_users)


def host_enter_maintenance():
    return esxi_host.enter_maintenance(_opts())


def host_exit_maintenance():
    return esxi_host.exit_maintenance(_opts())


def host_reboot(force=False):
    return esxi_host.reboot(_opts(), force=force)


def host_shutdown(force=False):
    return esxi_host.shutdown(_opts(), force=force)


def service_list():
    return esxi_service.list_(_opts())


def service_get(service):
    return esxi_service.get(_opts(), service)


def service_start(service):
    return esxi_service.start(_opts(), service)


def service_stop(service):
    return esxi_service.stop(_opts(), service)


def service_restart(service):
    return esxi_service.restart(_opts(), service)


def service_set_policy(service, policy):
    return esxi_service.set_policy(_opts(), service, policy)


def firewall_list():
    return esxi_firewall.list_(_opts())


def firewall_get(rule):
    return esxi_firewall.get(_opts(), rule)


def firewall_set_enabled(rule, enabled):
    return esxi_firewall.set_enabled(_opts(), rule, enabled)


def firewall_set_allowed_ips(rule, allowed_ips, all_ip=False):
    return esxi_firewall.set_allowed_ips(_opts(), rule, allowed_ips, all_ip=all_ip)


def ntp_get():
    return esxi_ntp.get(_opts())


def ntp_set_servers(servers):
    return esxi_ntp.set_servers(_opts(), servers)


def ntp_set_enabled(enabled):
    return esxi_ntp.set_enabled(_opts(), enabled)


def syslog_get():
    return esxi_syslog.get(_opts())


def syslog_set_servers(servers):
    return esxi_syslog.set_servers(_opts(), servers)


def syslog_set_log_level(level):
    return esxi_syslog.set_log_level(_opts(), level)


def advanced_list():
    return esxi_advanced.list_(_opts())


def advanced_get(key):
    return esxi_advanced.get(_opts(), key)


def advanced_set(key, value):
    return esxi_advanced.set_value(_opts(), key, value)
