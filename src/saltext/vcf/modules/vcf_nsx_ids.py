"""Execution module for NSX Distributed IDS/IPS."""

from saltext.vcf.clients import nsx_ids as c

__virtualname__ = "vcf_nsx_ids"


def __virtual__():
    return __virtualname__


# Global config


def get_global_config(profile=None):
    """Return the global IDS settings.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ids.get_global_config
    """
    return c.get_global_config(__opts__, profile=profile)


def set_global_config(profile=None, **spec):
    """Update the global IDS settings.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ids.set_global_config auto_update=True
    """
    return c.set_global_config(__opts__, profile=profile, **spec)


# Per-cluster


def list_cluster_configs(profile=None):
    """List per-cluster IDS configs.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ids.list_cluster_configs
    """
    return c.list_cluster_configs(__opts__, profile=profile)


def get_cluster_config(cluster_id, profile=None):
    """Return one cluster's IDS config.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ids.get_cluster_config <cluster_id>
    """
    return c.get_cluster_config(__opts__, cluster_id, profile=profile)


def set_cluster_config(cluster_id, profile=None, **spec):
    """Update a cluster's IDS config.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ids.set_cluster_config <cluster_id> ids_enabled=True
    """
    return c.set_cluster_config(__opts__, cluster_id, profile=profile, **spec)


# Profiles


def list_profiles(profile=None):
    """List IDS profiles.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ids.list_profiles
    """
    return c.list_profiles(__opts__, profile=profile)


def get_profile(profile_id, profile=None):
    """Return one IDS profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ids.get_profile <profile_id>
    """
    return c.get_profile(__opts__, profile_id, profile=profile)


def create_profile(profile_id, profile=None, **spec):
    """Create / update an IDS profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ids.create_profile <profile_id> severity='["CRITICAL"]'
    """
    return c.create_profile(__opts__, profile_id, profile=profile, **spec)


def delete_profile(profile_id, profile=None):
    """Delete an IDS profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ids.delete_profile <profile_id>
    """
    return c.delete_profile(__opts__, profile_id, profile=profile)


# Signatures (read-only)


def list_signatures(profile=None):
    """List IDS signatures (the built-in catalog).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ids.list_signatures
    """
    return c.list_signatures(__opts__, profile=profile)


def get_signature(signature_id, profile=None):
    """Return one IDS signature.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ids.get_signature <signature_id>
    """
    return c.get_signature(__opts__, signature_id, profile=profile)


# IDS policies + rules


def list_policies(domain="default", profile=None):
    """List IDS policies in a domain.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ids.list_policies
    """
    return c.list_policies(__opts__, domain=domain, profile=profile)


def get_policy(policy, domain="default", profile=None):
    """Return one IDS policy.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ids.get_policy <policy>
    """
    return c.get_policy(__opts__, policy, domain=domain, profile=profile)


def create_policy(policy, domain="default", profile=None, **spec):
    """Create / update an IDS policy.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ids.create_policy <policy> category=Infrastructure
    """
    return c.create_policy(__opts__, policy, domain=domain, profile=profile, **spec)


def delete_policy(policy, domain="default", profile=None):
    """Delete an IDS policy.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ids.delete_policy <policy>
    """
    return c.delete_policy(__opts__, policy, domain=domain, profile=profile)


def list_rules(policy, domain="default", profile=None):
    """List rules in an IDS policy.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ids.list_rules <policy>
    """
    return c.list_rules(__opts__, policy, domain=domain, profile=profile)


def get_rule(rule, policy, domain="default", profile=None):
    """Return one IDS rule.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ids.get_rule <rule> <policy>
    """
    return c.get_rule(__opts__, rule, policy, domain=domain, profile=profile)


def create_rule(rule, policy, domain="default", profile=None, **spec):
    """Create / update an IDS rule.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ids.create_rule <rule> <policy> action=DETECT ids_profiles='["..."]'
    """
    return c.create_rule(__opts__, rule, policy, domain=domain, profile=profile, **spec)


def delete_rule(rule, policy, domain="default", profile=None):
    """Delete an IDS rule.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_ids.delete_rule <rule> <policy>
    """
    return c.delete_rule(__opts__, rule, policy, domain=domain, profile=profile)
