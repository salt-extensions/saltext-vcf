"""Execution module for vSphere Lifecycle Manager (LCM) software depots."""

from saltext.vmware.clients import vcenter_lcm_depot as c

__virtualname__ = "vmware_vcenter_lcm_depot"


def __virtual__():
    return __virtualname__


# Offline


def list_offline(profile=None):
    """List offline depots.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_lcm_depot.list_offline
    """
    return c.list_offline(__opts__, profile=profile)


def get_offline(depot_id, profile=None):
    """Return one offline depot.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_lcm_depot.get_offline <depot_id>
    """
    return c.get_offline(__opts__, depot_id, profile=profile)


def create_offline(file_locator, profile=None, **spec):
    """Create an offline depot from an uploaded bundle.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_lcm_depot.create_offline file_locator=/storage/updatemgr/foo.zip
    """
    return c.create_offline(__opts__, file_locator, profile=profile, **spec)


def delete_offline(depot_id, profile=None):
    """Delete an offline depot.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_lcm_depot.delete_offline <depot_id>
    """
    return c.delete_offline(__opts__, depot_id, profile=profile)


# Online


def list_online(profile=None):
    """List online depots.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_lcm_depot.list_online
    """
    return c.list_online(__opts__, profile=profile)


def get_online(depot_id, profile=None):
    """Return one online depot.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_lcm_depot.get_online <depot_id>
    """
    return c.get_online(__opts__, depot_id, profile=profile)


def create_online(location, profile=None, **spec):
    """Create an online depot pointing at a URL.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_lcm_depot.create_online location=https://hostupdate.vmware.com/...
    """
    return c.create_online(__opts__, location, profile=profile, **spec)


def delete_online(depot_id, profile=None):
    """Delete an online depot.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_lcm_depot.delete_online <depot_id>
    """
    return c.delete_online(__opts__, depot_id, profile=profile)


# UMDS


def list_umds(profile=None):
    """List UMDS depots.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_lcm_depot.list_umds
    """
    return c.list_umds(__opts__, profile=profile)


def get_umds(depot_id, profile=None):
    """Return one UMDS depot.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_lcm_depot.get_umds <depot_id>
    """
    return c.get_umds(__opts__, depot_id, profile=profile)


def create_umds(location, profile=None, **spec):
    """Create a UMDS depot.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_lcm_depot.create_umds location=/var/umds/data
    """
    return c.create_umds(__opts__, location, profile=profile, **spec)


def delete_umds(depot_id, profile=None):
    """Delete a UMDS depot.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_lcm_depot.delete_umds <depot_id>
    """
    return c.delete_umds(__opts__, depot_id, profile=profile)


# Sync / content


def sync(profile=None):
    """Trigger a sync across all online / UMDS depots.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_lcm_depot.sync
    """
    return c.sync(__opts__, profile=profile)


def get_content(profile=None):
    """Return the bundles + components present in the depot.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vcenter_lcm_depot.get_content
    """
    return c.get_content(__opts__, profile=profile)
