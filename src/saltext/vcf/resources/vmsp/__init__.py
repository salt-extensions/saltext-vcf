"""
``vmsp`` resource type — one VMSP (VCF Security Platform) per resource ID.

Each ``vmsp`` resource maps to one VMSP endpoint, identified by an instance ID
under ``resources.vmsp.instances`` in the configured pillar subtree::

    resources:
      vmsp:
        instances:
          vcf-vmsp:
            host: vsp-platform.example.test
            username: admin@vsp.local
            password: secret
            verify_ssl: false

After :func:`discover` runs (via ``saltutil.refresh_resources``) the master can
target the instance directly::

    salt -C 'T@vmsp:vcf-vmsp' vcf_vmsp_ntp.compliant name=ntp servers='["10.0.0.250"]'

The current resource ID is conveyed via the loader-injected ``__resource__``
dunder, never as a parameter. All REST work is delegated to
:mod:`saltext.vcf.clients` so the standalone states and the Resources framework
share one implementation.
"""

import logging

import requests
import urllib3

from saltext.vcf.clients import vmsp_dns
from saltext.vcf.clients import vmsp_ntp
from saltext.vcf.clients import vmsp_syslog
from saltext.vcf.resources import pillar_resources_tree

log = logging.getLogger(__name__)

CONTEXT_KEY = "vmsp_resource"


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
        "pillar": {"saltext.vcf": {"vmsp": _instance_cfg(_resource_id())}},
    }


def init(opts):
    instances = pillar_resources_tree(opts).get("vmsp", {}).get("instances", {})
    __context__[CONTEXT_KEY] = {  # pylint: disable=undefined-variable
        "initialized": True,
        "instances": instances,
    }
    log.debug("vmsp resource init: managing %s", list(instances))


def initialized():
    return __context__.get(CONTEXT_KEY, {}).get(  # pylint: disable=undefined-variable
        "initialized", False
    )


def discover(opts):
    return list(pillar_resources_tree(opts).get("vmsp", {}).get("instances", {}))


def grains():
    rid = _resource_id()
    cfg = _instance_cfg(rid)
    return {
        "resource_type": "vmsp",
        "resource_id": rid,
        "host": cfg.get("host", ""),
    }


def grains_refresh():
    return grains()


def ping():
    """Probe the identity token endpoint to confirm VMSP is reachable."""
    cfg = _instance_cfg(_resource_id())
    host = cfg.get("host")
    verify = cfg.get("verify_ssl", True)
    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    try:
        resp = requests.post(
            f"https://{host}/api/v1/identity/token",
            data={
                "grant_type": "password",
                "username": cfg.get("username"),
                "password": cfg.get("password"),
            },
            headers={"content-type": "application/x-www-form-urlencoded"},
            verify=verify,
            timeout=10,
        )
        return resp.status_code == 200
    except requests.RequestException as exc:
        log.warning("vmsp ping failed for %s: %s", host, exc)
        return False


def shutdown(opts):
    __context__.pop(CONTEXT_KEY, None)  # pylint: disable=undefined-variable


# ---------------------------------------------------------------------------
# Per-resource operations (delegated to clients/)
# ---------------------------------------------------------------------------


def ntp_get():
    return vmsp_ntp.get(_opts())


def ntp_set(servers):
    return vmsp_ntp.set_(_opts(), servers)


def dns_get():
    return vmsp_dns.get(_opts())


def dns_set(servers):
    return vmsp_dns.set_(_opts(), servers)


def syslog_get():
    return vmsp_syslog.get(_opts())


def syslog_set(host, port=514, transport="tcp", insecure=False, cacert=None):
    return vmsp_syslog.set_(
        _opts(), host=host, port=port, transport=transport, insecure=insecure, cacert=cacert
    )
