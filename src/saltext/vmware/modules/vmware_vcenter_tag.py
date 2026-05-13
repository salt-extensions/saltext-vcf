"""Execution module for vCenter tags."""

from saltext.vmware.clients import vcenter_tag as r

__virtualname__ = "vmware_vcenter_tag"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List tag ids.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_tag.list_

    """
    return r.list_(__opts__, profile=profile)


def create(name, category_id, description="", profile=None):
    """Create a tag in a category.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_tag.create <name> <category_id> <description>

    """
    return r.create(__opts__, name, category_id, description=description, profile=profile)


def get(tag, profile=None):
    """Return a tag by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_tag.get <tag>
    """
    return r.get(__opts__, tag, profile=profile)


def update(tag, spec, profile=None):
    """PATCH a tag.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_tag.update <tag> spec='{"name": "newname"}'
    """
    return r.update(__opts__, tag, spec, profile=profile)


def delete(tag, profile=None):
    """Delete a tag by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_tag.delete <tag>

    """
    return r.delete(__opts__, tag, profile=profile)


def assign(tag, object_type, object_id, profile=None):
    """Attach a tag to an object.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_tag.assign <tag> <object_type> <object_id>

    """
    return r.assign(__opts__, tag, object_type, object_id, profile=profile)


def list_assigned(object_type, object_id, profile=None):
    """List tags attached to an object.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_tag.list_assigned <object_type> <object_id>

    """
    return r.list_assigned(__opts__, object_type, object_id, profile=profile)
