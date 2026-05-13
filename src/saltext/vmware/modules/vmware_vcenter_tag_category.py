"""Execution module for vCenter tag categories."""

from saltext.vmware.clients import vcenter_tag_category as r

__virtualname__ = "vmware_vcenter_tag_category"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List category IDs.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_tag_category.list_
    """
    return r.list_(__opts__, profile=profile)


def get(category_id, profile=None):
    """Return a category by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_tag_category.get <category_id>
    """
    return r.get(__opts__, category_id, profile=profile)


def create(name, cardinality="SINGLE", description="", associable_types=None, profile=None):
    """Create a tag category.

    *cardinality* is ``SINGLE`` or ``MULTIPLE``.
    *associable_types* is a list of inventory object types this category's tags
    can be applied to (empty list = any object type).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_tag_category.create owner cardinality=SINGLE associable_types='["VirtualMachine"]'
    """
    return r.create(
        __opts__,
        name,
        cardinality=cardinality,
        description=description,
        associable_types=associable_types,
        profile=profile,
    )


def update(category_id, spec, profile=None):
    """PATCH a tag category.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_tag_category.update <category_id> spec='{"description": "new"}'
    """
    return r.update(__opts__, category_id, spec, profile=profile)


def delete(category_id, profile=None):
    """Delete a tag category (and all its tags).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_tag_category.delete <category_id>
    """
    return r.delete(__opts__, category_id, profile=profile)
