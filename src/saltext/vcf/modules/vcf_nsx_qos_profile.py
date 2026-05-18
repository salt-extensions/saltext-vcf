"""Execution module for NSX QoS profiles."""

from saltext.vcf.clients import nsx_qos_profile as c

__virtualname__ = "vcf_nsx_qos_profile"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List QoS profiles.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_qos_profile.list_
    """
    return c.list_(__opts__, profile=profile)


def get(qos_profile, profile=None):
    """Return one QoS profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_qos_profile.get <qos_profile>
    """
    return c.get(__opts__, qos_profile, profile=profile)


def create(qos_profile, profile=None, **spec):
    """Create / update a QoS profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_qos_profile.create <id> class_of_service=3 dscp='{"mode":"TRUSTED","priority":0}'
    """
    return c.create(__opts__, qos_profile, profile=profile, **spec)


def delete(qos_profile, profile=None):
    """Delete a QoS profile.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_qos_profile.delete <qos_profile>
    """
    return c.delete(__opts__, qos_profile, profile=profile)
