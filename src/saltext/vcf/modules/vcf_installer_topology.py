"""Execution module for VCF Installer workflow pillar validation."""

from saltext.vcf.clients import installer_topology as c

__virtualname__ = "vcf_installer_topology"


def __virtual__():
    return __virtualname__


def validate(spec=None):
    """Validate the VCF Installer workflow pillar.

    If *spec* is omitted, reads the full ``saltext.vcf`` pillar subtree.
    """
    return c.validate(_resolve_spec(spec))


def _resolve_spec(spec):
    if spec is not None:
        return spec
    pillar = __opts__.get("pillar", {})  # noqa: F821
    return pillar.get("saltext.vcf", {}) or {}
