"""Execution module for VCF Operations adapter kinds and instances."""

from saltext.vcf.clients import vcfops_adapter as c

__virtualname__ = "vcf_vcfops_adapter"


def __virtual__():
    return __virtualname__


def list_():
    """List all adapter kinds.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_adapter.list_

    """
    return c.list_(__opts__)


def get(kind_key):
    """Get an adapter kind by key.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_adapter.get <kind_key>

    """
    return c.get(__opts__, kind_key)


def instance_list(profile=None):
    """List all configured adapter instances.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_adapter.instance_list

    """
    return c.instance_list(__opts__, profile=profile)


def instance_get(instance_id, profile=None):
    """Get a single adapter instance by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_adapter.instance_get <instance_id>

    """
    return c.instance_get(__opts__, instance_id, profile=profile)


def instance_get_or_none(instance_id, profile=None):
    """Get a single adapter instance by id, returning ``None`` if it does not exist.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_adapter.instance_get_or_none <instance_id>

    """
    return c.instance_get_or_none(__opts__, instance_id, profile=profile)


def instance_create(spec, profile=None):
    """Create an adapter instance from *spec*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_adapter.instance_create '{"name": "vcenter-prod", ...}'

    """
    return c.instance_create(__opts__, spec, profile=profile)


def instance_update(instance_id, spec, profile=None):
    """Update an existing adapter instance.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_adapter.instance_update <instance_id> '{"name": "vc-prod", ...}'

    """
    return c.instance_update(__opts__, instance_id, spec, profile=profile)


def instance_delete(instance_id, profile=None):
    """Delete an adapter instance.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_adapter.instance_delete <instance_id>

    """
    return c.instance_delete(__opts__, instance_id, profile=profile)


def instance_start(instance_id, profile=None):
    """Start monitoring on an adapter instance.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_adapter.instance_start <instance_id>

    """
    return c.instance_start(__opts__, instance_id, profile=profile)


def instance_stop(instance_id, profile=None):
    """Stop monitoring on an adapter instance.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_adapter.instance_stop <instance_id>

    """
    return c.instance_stop(__opts__, instance_id, profile=profile)
