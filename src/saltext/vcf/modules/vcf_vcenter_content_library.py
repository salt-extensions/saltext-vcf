"""Execution module for vCenter Content Library."""

from saltext.vcf.clients import vcenter_content_library as c

__virtualname__ = "vcf_vcenter_content_library"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List .

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.list_

    """
    return c.list_(__opts__, profile=profile)


def get(library_id, profile=None):
    """Get.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.get <library_id>

    """
    return c.get(__opts__, library_id, profile=profile)


def list_local(profile=None):
    """List local.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.list_local

    """
    return c.list_local(__opts__, profile=profile)


def create_local(name, storage_backings, profile=None, **spec):
    """Create local.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.create_local <name> <storage_backings>

    """
    return c.create_local(__opts__, name, storage_backings, profile=profile, **spec)


def delete_local(library_id, profile=None):
    """Delete local.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.delete_local <library_id>

    """
    return c.delete_local(__opts__, library_id, profile=profile)


def list_subscribed(profile=None):
    """List subscribed.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.list_subscribed

    """
    return c.list_subscribed(__opts__, profile=profile)


def create_subscribed(name, subscription_url, storage_backings, profile=None, **spec):
    """Create subscribed.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.create_subscribed <name> <subscription_url> <storage_backings>

    """
    return c.create_subscribed(
        __opts__, name, subscription_url, storage_backings, profile=profile, **spec
    )


def list_items(library_id, profile=None):
    """List items.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.list_items <library_id>

    """
    return c.list_items(__opts__, library_id, profile=profile)


def get_item(item_id, profile=None):
    """Get item.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.get_item <item_id>

    """
    return c.get_item(__opts__, item_id, profile=profile)


def delete_item(item_id, profile=None):
    """Delete item.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.delete_item <item_id>

    """
    return c.delete_item(__opts__, item_id, profile=profile)


# -- library write paths --------------------------------------------------


def update_local(library_id, spec, profile=None):
    """PATCH a local library.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.update_local <library_id> spec='{"name": "new"}'
    """
    return c.update_local(__opts__, library_id, spec, profile=profile)


def update_subscribed(library_id, spec, profile=None):
    """PATCH a subscribed library.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.update_subscribed <library_id> spec='{...}'
    """
    return c.update_subscribed(__opts__, library_id, spec, profile=profile)


def sync_subscribed(library_id, profile=None):
    """Force a subscribed library to sync.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.sync_subscribed <library_id>
    """
    return c.sync_subscribed(__opts__, library_id, profile=profile)


def publish_library(library_id, subscriptions=None, profile=None):
    """Publish a local library to subscribers (all subscribers if *subscriptions* is None).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.publish_library <library_id>
    """
    return c.publish_library(__opts__, library_id, subscriptions=subscriptions, profile=profile)


def find_libraries(name=None, type=None, profile=None):  # pylint: disable=redefined-builtin
    """Search libraries by name/type.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.find_libraries name=base type=LOCAL
    """
    return c.find_libraries(__opts__, name=name, type=type, profile=profile)


# -- item write paths -----------------------------------------------------


def create_item(library_id, name, type, profile=None, **spec):  # pylint: disable=redefined-builtin
    """Create an empty library item.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.create_item <library_id> myitem ovf
    """
    return c.create_item(__opts__, library_id, name, type, profile=profile, **spec)


def update_item(item_id, spec, profile=None):
    """PATCH a library item.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.update_item <item_id> spec='{"name": "new"}'
    """
    return c.update_item(__opts__, item_id, spec, profile=profile)


def find_items(
    library_id=None, name=None, type=None, profile=None
):  # pylint: disable=redefined-builtin
    """Search items by library, name, and/or type.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.find_items library_id=<id> name=foo
    """
    return c.find_items(__opts__, library_id=library_id, name=name, type=type, profile=profile)


# -- update sessions ------------------------------------------------------


def update_session_create(item_id, profile=None, **spec):
    """Open an update session against an item.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.update_session_create <item_id>
    """
    return c.update_session_create(__opts__, item_id, profile=profile, **spec)


def update_session_get(session_id, profile=None):
    """Return update session status.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.update_session_get <session_id>
    """
    return c.update_session_get(__opts__, session_id, profile=profile)


def update_session_complete(session_id, profile=None):
    """Mark an update session complete (commits uploads).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.update_session_complete <session_id>
    """
    return c.update_session_complete(__opts__, session_id, profile=profile)


def update_session_cancel(session_id, profile=None):
    """Cancel an update session (discards uploads).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.update_session_cancel <session_id>
    """
    return c.update_session_cancel(__opts__, session_id, profile=profile)


def update_session_fail(session_id, error, profile=None):
    """Mark an update session failed with *error*.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.update_session_fail <session_id> 'error message'
    """
    return c.update_session_fail(__opts__, session_id, error, profile=profile)


def update_session_keep_alive(session_id, profile=None):
    """Refresh an update session lease.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.update_session_keep_alive <session_id>
    """
    return c.update_session_keep_alive(__opts__, session_id, profile=profile)


def update_session_add_file(session_id, name, source_type="PUSH", profile=None, **spec):
    """Register a file for upload in an update session.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.update_session_add_file <session_id> disk.vmdk
    """
    return c.update_session_add_file(
        __opts__, session_id, name, source_type=source_type, profile=profile, **spec
    )


def update_session_list_files(session_id, profile=None):
    """List files registered in an update session.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.update_session_list_files <session_id>
    """
    return c.update_session_list_files(__opts__, session_id, profile=profile)


# -- OVF deploy / create_from_vm ------------------------------------------


def ovf_deploy(library_item_id, deployment_target, deployment_spec, profile=None):
    """Deploy an OVF library item to a vCenter target.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.ovf_deploy <item_id> '{"resource_pool_id": "..."}' '{"name": "vm-1"}'
    """
    return c.ovf_deploy(
        __opts__, library_item_id, deployment_target, deployment_spec, profile=profile
    )


def ovf_filter(library_item_id, deployment_target, profile=None):
    """Return inventory bindings for an OVF item against a deployment target.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.ovf_filter <item_id> '{"resource_pool_id": "..."}'
    """
    return c.ovf_filter(__opts__, library_item_id, deployment_target, profile=profile)


def ovf_create_from_vm(vm_id, create_spec, profile=None):
    """Export a VM as a new OVF library item.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.ovf_create_from_vm <vm_id> '{...}'
    """
    return c.ovf_create_from_vm(__opts__, vm_id, create_spec, profile=profile)


# -- VM template library items (vSphere 6.7+) -----------------------------


def vm_template_get(item_id, profile=None):
    """Return a VM-template library item.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.vm_template_get <item_id>
    """
    return c.vm_template_get(__opts__, item_id, profile=profile)


def vm_template_create(create_spec, profile=None):
    """Capture a VM as a new VM-template library item.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.vm_template_create '{...}'
    """
    return c.vm_template_create(__opts__, create_spec, profile=profile)


def vm_template_deploy(item_id, deploy_spec, profile=None):
    """Deploy a new VM from a VM-template library item.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcenter_content_library.vm_template_deploy <item_id> '{...}'
    """
    return c.vm_template_deploy(__opts__, item_id, deploy_spec, profile=profile)
