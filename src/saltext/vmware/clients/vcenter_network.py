"""Client for vCenter networks (/api/vcenter/network) — read-only."""

from saltext.vmware.utils import vcenter

PATH = "/api/vcenter/network"


def list_(opts, profile=None):
    """List networks (DVPGs and standard port groups visible to vCenter)."""
    return vcenter.api_get(opts, PATH, profile=profile)
