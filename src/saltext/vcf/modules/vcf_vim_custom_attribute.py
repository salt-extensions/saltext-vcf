"""Execution module for vCenter custom attributes (SOAP)."""

from saltext.vcf.clients import vim_custom_attribute as c

__virtualname__ = "vcf_vim_custom_attribute"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_custom_attribute.list_

    """
    return c.list_(__opts__, profile=profile)


def get(name, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_custom_attribute.get <name>

    """
    return c.get(__opts__, name, profile=profile)


def add(name, managed_object_type=None, profile=None):
    """Add.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_custom_attribute.add <name> <managed_object_type>

    """
    return c.add(__opts__, name, managed_object_type=managed_object_type, profile=profile)


def remove(name_or_key, profile=None):
    """Remove.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_custom_attribute.remove <name_or_key>

    """
    return c.remove(__opts__, name_or_key, profile=profile)


def set_value(entity_mo_id, name, value, entity_type=None, profile=None):
    """Set value.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_custom_attribute.set_value <entity_mo_id> <name> <value> <entity_type>

    """
    return c.set_value(
        __opts__, entity_mo_id, name, value, entity_type=entity_type, profile=profile
    )
