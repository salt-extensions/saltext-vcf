"""Execution module for ESXi firewall rulesets (vCenter-routed SOAP)."""

from saltext.vcf.clients import vim_host_firewall as c

__virtualname__ = "vcf_vim_host_firewall"


def __virtual__():
    return __virtualname__


def get_all(host, profile=None):
    """Return all firewall rulesets on *host*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_firewall.get_all esxi-01
    """
    return c.get_all(__opts__, host, profile=profile)


def get(host, ruleset_name, profile=None):
    """Return one firewall ruleset by name.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_firewall.get esxi-01 CIMHttpServer
    """
    return c.get(__opts__, host, ruleset_name, profile=profile)


def set_enabled(host, ruleset_name, enabled, profile=None):
    """Enable or disable a firewall ruleset.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_firewall.set_enabled esxi-01 CIMHttpServer enabled=true
    """
    return c.set_enabled(__opts__, host, ruleset_name, enabled, profile=profile)


def set_config(host, firewall_config, profile=None):
    """Apply a firewall rule-config dict (name/enabled/allowed_hosts).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_firewall.set_config esxi-01 '{"name": "CIMHttpServer", "enabled": true}'
    """
    return c.set_config(__opts__, host, firewall_config, profile=profile)


def set_all_configs(host, firewall_configs, profile=None):
    """Apply a list of firewall rule-config dicts in one call.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_firewall.set_all_configs esxi-01 '[{"name": "CIMHttpServer", "enabled": true}]'
    """
    return c.set_all_configs(__opts__, host, firewall_configs, profile=profile)
