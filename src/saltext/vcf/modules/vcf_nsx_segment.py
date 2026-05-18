"""Execution module for NSX segments."""

from saltext.vcf.clients import nsx_segment as r

__virtualname__ = "vcf_nsx_segment"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List all segments.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_segment.list_

    """
    return r.list_(__opts__, profile=profile)


def get(segment, profile=None):
    """Return a segment by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_segment.get <segment>

    """
    return r.get(__opts__, segment, profile=profile)


def create(segment, profile=None, **spec):
    """Create or update a segment (PUT).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_segment.create <segment>

    """
    return r.create(__opts__, segment, profile=profile, **spec)


def delete(segment, profile=None):
    """Delete a segment by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_segment.delete <segment>

    """
    return r.delete(__opts__, segment, profile=profile)
