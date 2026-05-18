"""Execution module for the vSphere 9 cluster Configuration Profile API.

This is the supported surface on VCF 9.0+ for managing per-host config
(services, firewall, NTP, syslog, advanced settings) on hosts that are
joined to a vCenter cluster. The profile applies declaratively to every
host in the cluster.

Quick reference::

    # Status
    salt-call vcf_cluster_config.enablement_get domain-c9
    salt-call vcf_cluster_config.configuration_get domain-c9
    salt-call vcf_cluster_config.schema_get domain-c9

    # Drafts
    salt-call vcf_cluster_config.drafts_list domain-c9
    salt-call vcf_cluster_config.draft_create domain-c9
    salt-call vcf_cluster_config.draft_get domain-c9 <draft_id>
    salt-call vcf_cluster_config.draft_update_configuration domain-c9 <draft_id> '<json>'
    salt-call vcf_cluster_config.draft_apply domain-c9 <draft_id>
"""

from saltext.vcf.clients import cluster_config as c

__virtualname__ = "vcf_cluster_config"


def __virtual__():
    return __virtualname__


def enablement_get(cluster, profile=None):
    """Enablement get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_cluster_config.enablement_get <cluster>

    """
    return c.enablement_get(__opts__, cluster, profile=profile)


def schema_get(cluster, profile=None):
    """Schema get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_cluster_config.schema_get <cluster>

    """
    return c.schema_get(__opts__, cluster, profile=profile)


def configuration_get(cluster, profile=None):
    """Configuration get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_cluster_config.configuration_get <cluster>

    """
    return c.configuration_get(__opts__, cluster, profile=profile)


def drafts_list(cluster, profile=None):
    """Drafts list.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_cluster_config.drafts_list <cluster>

    """
    return c.drafts_list(__opts__, cluster, profile=profile)


def draft_create(cluster, body=None, profile=None):
    """Draft create.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_cluster_config.draft_create <cluster> <body>

    """
    return c.draft_create(__opts__, cluster, body=body, profile=profile)


def draft_get(cluster, draft_id, profile=None):
    """Draft get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_cluster_config.draft_get <cluster> <draft_id>

    """
    return c.draft_get(__opts__, cluster, draft_id, profile=profile)


def draft_get_configuration(cluster, draft_id, profile=None):
    """Draft get configuration.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_cluster_config.draft_get_configuration <cluster> <draft_id>

    """
    return c.draft_get_configuration(__opts__, cluster, draft_id, profile=profile)


def draft_update_configuration(cluster, draft_id, body, profile=None):
    """Draft update configuration.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_cluster_config.draft_update_configuration <cluster> <draft_id> <body>

    """
    return c.draft_update_configuration(__opts__, cluster, draft_id, body, profile=profile)


def draft_delete(cluster, draft_id, profile=None):
    """Draft delete.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_cluster_config.draft_delete <cluster> <draft_id>

    """
    return c.draft_delete(__opts__, cluster, draft_id, profile=profile)


def draft_apply(cluster, draft_id, profile=None):
    """Draft apply.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_cluster_config.draft_apply <cluster> <draft_id>

    """
    return c.draft_apply(__opts__, cluster, draft_id, profile=profile)


def last_apply_result(cluster, profile=None):
    """Last apply result.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_cluster_config.last_apply_result <cluster>

    """
    return c.last_apply_result(__opts__, cluster, profile=profile)


def last_compliance_result(cluster, profile=None):
    """Last compliance result.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_cluster_config.last_compliance_result <cluster>

    """
    return c.last_compliance_result(__opts__, cluster, profile=profile)
