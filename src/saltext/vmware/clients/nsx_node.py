"""NSX Management API — node info (singleton)."""

from saltext.vmware.utils import nsx

PATH = "/api/v1/node"


def get(opts, profile=None):
    """Return NSX node info: version, kernel, hostname, services."""
    return nsx.api_get(opts, PATH, profile=profile)
