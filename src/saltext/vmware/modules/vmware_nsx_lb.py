"""Execution module for NSX Load Balancer (T7)."""

from saltext.vmware.clients import nsx_lb_app_profile as appprof
from saltext.vmware.clients import nsx_lb_monitor as monitor
from saltext.vmware.clients import nsx_lb_persistence as persistence
from saltext.vmware.clients import nsx_lb_pool as pool
from saltext.vmware.clients import nsx_lb_service as service
from saltext.vmware.clients import nsx_lb_virtual_server as vs

__virtualname__ = "vmware_nsx_lb"


def __virtual__():
    return __virtualname__


# Services


def list_services(profile=None):
    """List LB services.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.list_services
    """
    return service.list_(__opts__, profile=profile)


def get_service(lb_service, profile=None):
    """Return one LB service.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.get_service <lb_service>
    """
    return service.get(__opts__, lb_service, profile=profile)


def create_service(lb_service, profile=None, **spec):
    """Create / update an LB service (PUT semantics).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.create_service <lb_service> size=SMALL
    """
    return service.create(__opts__, lb_service, profile=profile, **spec)


def delete_service(lb_service, profile=None):
    """Delete an LB service.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.delete_service <lb_service>
    """
    return service.delete(__opts__, lb_service, profile=profile)


# Virtual servers


def list_virtual_servers(profile=None):
    """List LB virtual servers.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.list_virtual_servers
    """
    return vs.list_(__opts__, profile=profile)


def get_virtual_server(virtual_server, profile=None):
    """Return one virtual server.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.get_virtual_server <virtual_server>
    """
    return vs.get(__opts__, virtual_server, profile=profile)


def create_virtual_server(virtual_server, profile=None, **spec):
    """Create / update a virtual server.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.create_virtual_server <vs> ip_address=10.0.0.1 ports='["80"]'
    """
    return vs.create(__opts__, virtual_server, profile=profile, **spec)


def delete_virtual_server(virtual_server, profile=None):
    """Delete a virtual server.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.delete_virtual_server <virtual_server>
    """
    return vs.delete(__opts__, virtual_server, profile=profile)


# Pools


def list_pools(profile=None):
    """List LB pools.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.list_pools
    """
    return pool.list_(__opts__, profile=profile)


def get_pool(pool_id, profile=None):
    """Return one pool.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.get_pool <pool_id>
    """
    return pool.get(__opts__, pool_id, profile=profile)


def create_pool(pool_id, profile=None, **spec):
    """Create / update a pool.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.create_pool <pool_id> algorithm=ROUND_ROBIN
    """
    return pool.create(__opts__, pool_id, profile=profile, **spec)


def delete_pool(pool_id, profile=None):
    """Delete a pool.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.delete_pool <pool_id>
    """
    return pool.delete(__opts__, pool_id, profile=profile)


# Monitor profiles


def list_monitors(profile=None):
    """List LB monitor profiles.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.list_monitors
    """
    return monitor.list_(__opts__, profile=profile)


def get_monitor(monitor_id, profile=None):
    """Return one monitor profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.get_monitor <monitor_id>
    """
    return monitor.get(__opts__, monitor_id, profile=profile)


def create_monitor(monitor_id, resource_type, profile=None, **spec):
    """Create / update a monitor profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.create_monitor <id> LBHttpMonitorProfile request_url=/healthz
    """
    return monitor.create(__opts__, monitor_id, resource_type, profile=profile, **spec)


def delete_monitor(monitor_id, profile=None):
    """Delete a monitor profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.delete_monitor <monitor_id>
    """
    return monitor.delete(__opts__, monitor_id, profile=profile)


# App profiles


def list_app_profiles(profile=None):
    """List LB application profiles.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.list_app_profiles
    """
    return appprof.list_(__opts__, profile=profile)


def get_app_profile(app_profile, profile=None):
    """Return one app profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.get_app_profile <app_profile>
    """
    return appprof.get(__opts__, app_profile, profile=profile)


def create_app_profile(app_profile, resource_type, profile=None, **spec):
    """Create / update an app profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.create_app_profile <id> LBHttpProfile
    """
    return appprof.create(__opts__, app_profile, resource_type, profile=profile, **spec)


def delete_app_profile(app_profile, profile=None):
    """Delete an app profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.delete_app_profile <app_profile>
    """
    return appprof.delete(__opts__, app_profile, profile=profile)


# Persistence profiles


def list_persistence_profiles(profile=None):
    """List LB persistence profiles.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.list_persistence_profiles
    """
    return persistence.list_(__opts__, profile=profile)


def get_persistence_profile(persistence_id, profile=None):
    """Return one persistence profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.get_persistence_profile <persistence_id>
    """
    return persistence.get(__opts__, persistence_id, profile=profile)


def create_persistence_profile(persistence_id, resource_type, profile=None, **spec):
    """Create / update a persistence profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.create_persistence_profile <id> LBSourceIpPersistenceProfile
    """
    return persistence.create(__opts__, persistence_id, resource_type, profile=profile, **spec)


def delete_persistence_profile(persistence_id, profile=None):
    """Delete a persistence profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_nsx_lb.delete_persistence_profile <persistence_id>
    """
    return persistence.delete(__opts__, persistence_id, profile=profile)
