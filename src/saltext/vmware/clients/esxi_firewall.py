"""ESXi firewall rules — enable/disable rules and manage allowed-IP lists."""

import requests

from saltext.vmware.utils import esxi

PATH = "/api/esx/firewall/rules"


def list_(opts, profile=None):
    return esxi.api_get(opts, PATH, profile=profile)


def get(opts, rule, profile=None):
    return esxi.api_get(opts, f"{PATH}/{rule}", profile=profile)


def get_or_none(opts, rule, profile=None):
    try:
        return get(opts, rule, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def set_enabled(opts, rule, enabled, profile=None):
    return esxi.api_patch(opts, f"{PATH}/{rule}", body={"enabled": bool(enabled)}, profile=profile)


def set_allowed_ips(opts, rule, allowed_ips, all_ip=False, profile=None):
    """Replace the allowed-IP list for *rule*.

    *allowed_ips* is a list of strings (CIDR or single addresses).
    *all_ip* True opens the rule to all sources; the list is then ignored
    by ESXi.
    """
    body = {"allowed_hosts": {"all_ip": bool(all_ip), "ip_addresses": list(allowed_ips)}}
    return esxi.api_patch(opts, f"{PATH}/{rule}", body=body, profile=profile)
