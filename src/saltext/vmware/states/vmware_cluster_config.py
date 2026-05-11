"""State module for the vSphere 9 cluster Configuration Profile API.

The state below operates at the **cluster** level — the profile applies to
every host in the cluster (vSphere 9 has no per-host imperative REST for
these knobs). Use this to declaratively manage host services, NTP, syslog,
firewall, advanced settings, etc.

Example::

    Set NTP servers cluster-wide:
      vmware_cluster_config.profile_value:
        - name: domain-c9
        - key: profile.esx.health.ntp_health.servers
        - value:
          - pool.ntp.org
          - time.cloudflare.com
"""

import requests

from saltext.vmware.clients import cluster_config as c

__virtualname__ = "vmware_cluster_config"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def enabled(name, profile=None):
    """Ensure Configuration Profile is enabled on cluster *name*."""
    ret = _ret(name)
    current = c.enablement_get(__opts__, name, profile=profile) or {}
    if current.get("enabled"):
        ret["comment"] = f"Configuration Profile already enabled on {name}"
        return ret
    ret["result"] = False
    ret["comment"] = (
        f"Configuration Profile not enabled on cluster {name}; enable it via "
        "vSphere UI or vLCM tooling before applying this state."
    )
    return ret


def profile_value(name, key, value, profile=None):
    """Ensure a specific Configuration Profile *key* on cluster *name* equals *value*.

    *key* is a dotted JSON-Schema-style path (e.g.
    ``profile.esx.health.ntp_health.servers``). Comparison is exact. When a
    change is needed, the state creates a draft, patches just that key, then
    applies the draft.
    """
    ret = _ret(name)
    try:
        current_doc = c.configuration_get(__opts__, name, profile=profile)
    except requests.HTTPError as exc:
        ret["result"] = False
        ret["comment"] = f"Could not read cluster {name} configuration: {exc}"
        return ret
    if current_doc is None:
        ret["result"] = False
        ret["comment"] = (
            f"Cluster {name} has no Configuration Profile yet (not vLCM-managed?). "
            "Enable it before applying this state."
        )
        return ret

    current_value = c.get_profile_value(current_doc, key)
    if current_value == value:
        ret["comment"] = f"{key} on {name} already {value!r}"
        return ret

    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"{key} on {name} would change from {current_value!r} to {value!r}"
        return ret

    draft_id = c.draft_create(__opts__, name, profile=profile)
    draft_doc = c.draft_get_configuration(__opts__, name, draft_id, profile=profile)
    c.set_profile_value(draft_doc, key, value)
    c.draft_update_configuration(__opts__, name, draft_id, draft_doc, profile=profile)
    c.draft_apply(__opts__, name, draft_id, profile=profile)
    ret["changes"] = {key: {"old": current_value, "new": value}}
    ret["comment"] = f"{key} on {name} updated"
    return ret
