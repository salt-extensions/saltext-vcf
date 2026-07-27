"""Execution module for NSX Manager LDAP/AD identity sources."""

from saltext.vcf.clients import nsx_identity_source as c

__virtualname__ = "vcf_nsx_identity_source"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List all LDAP identity sources registered on NSX Manager.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_identity_source.list_

    """
    return c.list_(__opts__, profile=profile)


def get(source_id, profile=None):
    """Get one LDAP identity source by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_identity_source.get <source_id>

    """
    return c.get(__opts__, source_id, profile=profile)


def create(body, profile=None):
    """Create an LDAP identity source. *body* is the NSX API payload.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_identity_source.create '{"name": "corp-ad", ...}'

    """
    return c.create(__opts__, body, profile=profile)


def update(source_id, body, profile=None):
    """Update an LDAP identity source by id (PUT).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_identity_source.update <source_id> <body>

    """
    return c.update(__opts__, source_id, body, profile=profile)


def delete(source_id, profile=None):
    """Delete an LDAP identity source by id.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_nsx_identity_source.delete <source_id>

    """
    return c.delete(__opts__, source_id, profile=profile)
