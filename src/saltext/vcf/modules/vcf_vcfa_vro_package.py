"""Execution module for VCF Automation vRO packages."""

from saltext.vcf.clients import vcfa_vro_package as c

__virtualname__ = "vcf_vcfa_vro_package"


def __virtual__():
    return __virtualname__


def list_(profile=None):
    """List vRO packages.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_vro_package.list_
    """
    return c.list_(__opts__, profile=profile)


def get(name, profile=None):
    """Get one vRO package by name."""
    return c.get(__opts__, name, profile=profile)


def get_or_none(name, profile=None):
    """Get one vRO package by name, or ``None`` on 404."""
    return c.get_or_none(__opts__, name, profile=profile)


def import_(name, package_bytes, overwrite=False, profile=None):
    """Import a ``.package`` payload."""
    return c.import_(__opts__, name, package_bytes, overwrite=overwrite, profile=profile)


def delete(name, option=None, profile=None):
    """Delete a vRO package."""
    return c.delete(__opts__, name, option=option, profile=profile)


def export_(name, profile=None):
    """Export a vRO package; returns the raw ``.package`` bytes."""
    return c.export_(__opts__, name, profile=profile)
