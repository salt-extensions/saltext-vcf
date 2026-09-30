"""State module for ESXi firewall rulesets (vCenter-routed SOAP).

Port of ``vmware_esxi.firewall_config`` / ``firewall_configs`` states,
with drift reporting via :mod:`saltext.vcf.utils.drift`.
"""

from saltext.vcf.clients import vim_host_firewall as c
from saltext.vcf.utils.drift import drift_report

__virtualname__ = "vcf_vim_host_firewall"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def _desired_config(name, value):
    """Normalize the state args into a rule-config dict."""
    if isinstance(value, dict):
        cfg = dict(value)
        cfg["name"] = name
        return cfg
    return {"name": name, "enabled": bool(value)}


def firewall_config(
    name,
    host,
    value,
    profile=None,
    drift_level=None,
):
    """Ensure firewall ruleset *name* on *host* matches *value*.

    *value* is either a bool (enabled/disabled) or a rule-config dict
    with ``enabled`` / ``allowed_hosts`` (``all_ip``, ``ip_address``,
    ``ip_network``).

    .. code-block:: yaml

        Enable CIM HTTP:
          vcf_vim_host_firewall.firewall_config:
            - host: esxi-01
            - name: CIMHttpServer
            - value: true
    """
    ret = _ret(name)
    current = c.get_or_none(__opts__, host, name, profile=profile)
    desired = _desired_config(name, value)
    if current is None:
        ret["result"] = False
        ret["comment"] = f"Firewall ruleset {name!r} not found on {host}."
        return ret
    # Build comparable "current-config" shape from the live ruleset.
    cur_cfg = {
        "name": name,
        "enabled": current["enabled"],
        "allowed_hosts": {
            "all_ip": current["allowed_hosts"]["all_ip"],
            "ip_address": sorted(current["allowed_hosts"]["ip_address"]),
            "ip_network": sorted(current["allowed_hosts"]["ip_network"]),
        },
    }
    desired_cfg = {
        "name": name,
        "enabled": bool(desired.get("enabled", cur_cfg["enabled"])),
        "allowed_hosts": {
            "all_ip": bool(desired.get("allowed_hosts", {}).get("all_ip", cur_cfg["allowed_hosts"]["all_ip"])),
            "ip_address": sorted(
                desired.get("allowed_hosts", {}).get("ip_address", cur_cfg["allowed_hosts"]["ip_address"])
            ),
            "ip_network": sorted(
                desired.get("allowed_hosts", {}).get("ip_network", cur_cfg["allowed_hosts"]["ip_network"])
            ),
        },
    }
    drift = drift_report(cur_cfg, desired_cfg, diff_level=drift_level)
    if not drift:
        ret["comment"] = f"Firewall ruleset {name!r} on {host} already matches."
        return ret
    ret["changes"] = drift
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Firewall ruleset {name!r} on {host} would be updated."
        return ret
    c.set_config(__opts__, host, desired_cfg, profile=profile)
    ret["comment"] = f"Firewall ruleset {name!r} on {host} updated."
    return ret


def firewall_configs(name, host, config, profile=None, drift_level=None):
    """Ensure a batch of firewall rulesets on *host*.

    *config* is a list of rule-config dicts (each with ``name``) or
    ``{ruleset: value}`` mapping. Reports aggregate drift via
    :func:`saltext.vcf.utils.drift.drift_report`.

    .. code-block:: yaml

        Firewall hardening:
          vcf_vim_host_firewall.firewall_configs:
            - host: esxi-01
            - config:
                CIMHttpServer: false
                CIMHttpsServer: false
                sshServer: false
    """
    ret = _ret(name)
    if isinstance(config, dict):
        configs = [_desired_config(k, v) for k, v in config.items()]
    else:
        configs = [dict(c) for c in (config or [])]

    current_all = c.get_all(__opts__, host, profile=profile)
    cur_cfg = {
        c2["name"]: {
            "enabled": info["enabled"],
            "allowed_hosts": {
                "all_ip": info["allowed_hosts"]["all_ip"],
                "ip_address": sorted(info["allowed_hosts"]["ip_address"]),
                "ip_network": sorted(info["allowed_hosts"]["ip_network"]),
            },
        }
        for c2 in configs
        for info in [current_all.get(c2["name"])]
        if info is not None
    }
    desired_cfg = {}
    for c2 in configs:
        desired_cfg[c2["name"]] = {
            "enabled": bool(c2.get("enabled", (cur_cfg.get(c2["name"]) or {}).get("enabled", False))),
            "allowed_hosts": {
                "all_ip": bool(
                    c2.get("allowed_hosts", {}).get(
                        "all_ip", (cur_cfg.get(c2["name"]) or {}).get("allowed_hosts", {}).get("all_ip", False)
                    )
                ),
                "ip_address": sorted(
                    c2.get("allowed_hosts", {}).get(
                        "ip_address",
                        (cur_cfg.get(c2["name"]) or {}).get("allowed_hosts", {}).get("ip_address", []),
                    )
                ),
                "ip_network": sorted(
                    c2.get("allowed_hosts", {}).get(
                        "ip_network",
                        (cur_cfg.get(c2["name"]) or {}).get("allowed_hosts", {}).get("ip_network", []),
                    )
                ),
            },
        }
    drift = drift_report(cur_cfg, desired_cfg, diff_level=drift_level)
    if not drift:
        ret["comment"] = f"Firewall rulesets on {host} already match."
        return ret
    ret["changes"] = drift
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Firewall rulesets on {host} would be updated."
        return ret
    missing = [c2["name"] for c2 in configs if c2["name"] not in current_all]
    if missing:
        ret["result"] = False
        ret["comment"] = f"Firewall rulesets not found on {host}: {missing}"
        return ret
    c.set_all_configs(__opts__, host, configs, profile=profile)
    ret["comment"] = f"Firewall rulesets on {host} updated."
    return ret
