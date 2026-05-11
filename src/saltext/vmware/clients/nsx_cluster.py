"""NSX Management API — cluster status (singleton)."""

from saltext.vmware.utils import nsx


def status(opts, profile=None):
    """Return cluster status: cluster_id, mgmt/control statuses, overall_status."""
    return nsx.api_get(opts, "/api/v1/cluster/status", profile=profile)
