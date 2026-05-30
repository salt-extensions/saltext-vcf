"""Execution module for reference ``vcf_automation`` topology compatibility."""

from saltext.vcf.clients import automation_topology as c

__virtualname__ = "vcf_automation_topology"


def __virtual__():
    return __virtualname__


def normalize(pillar=None):
    """Translate reference ``vcf_automation`` pillar to ``saltext.vcf`` shape."""
    return c.normalize(pillar or __opts__.get("pillar", {}))  # noqa: F821


def normalized_pillar(pillar=None):
    """Return pillar with ``saltext.vcf`` populated from ``vcf_automation``."""
    return c.normalized_pillar(pillar or __opts__.get("pillar", {}))  # noqa: F821
