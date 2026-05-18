"""SDDC Manager cluster expand / shrink / delete operations.

The list/get surface lives in :mod:`saltext.vcf.clients.sddc_cluster`;
this module adds the mutating lifecycle that ``sddc_cluster`` was missing.
Every call returns an async task; pair with :mod:`sddc_tasks` to poll.
"""

from saltext.vcf.utils import sddc

PATH = "/v1/clusters"


def validate(opts, spec, profile=None):
    """Validate a cluster spec (expand/create) before applying."""
    return sddc.api_post(opts, f"{PATH}/validations", body=spec, profile=profile)


def create(opts, spec, profile=None):
    """Create a new cluster in an existing workload domain. Returns task body."""
    return sddc.api_post(opts, PATH, body=spec, profile=profile)


def update(opts, cluster_id, spec, profile=None):
    """Generic cluster update — expand (add hosts), shrink (remove hosts),
    mark for deletion. *spec* shape per SDDC API ``ClusterUpdateSpec``.
    """
    return sddc.api_patch(opts, f"{PATH}/{cluster_id}", body=spec, profile=profile)


def delete(opts, cluster_id, profile=None):
    return sddc.api_delete(opts, f"{PATH}/{cluster_id}", profile=profile)


def expand(opts, cluster_id, host_specs, profile=None):
    """Add hosts to a cluster. *host_specs* is a list of ``ClusterExpansionSpec.hostSpecs``.

    Wraps the generic ``update`` with an expansion spec.
    """
    spec = {"clusterExpansionSpec": {"hostSpecs": list(host_specs)}}
    return update(opts, cluster_id, spec, profile=profile)


def shrink(opts, cluster_id, host_ids, force=False, profile=None):
    """Remove hosts from a cluster.

    *host_ids* is a list of SDDC host UUIDs; *force* skips the
    pre-removal validation (use with care).
    """
    spec = {
        "clusterCompactionSpec": {
            "hosts": [{"id": h} for h in host_ids],
            "force": bool(force),
        }
    }
    return update(opts, cluster_id, spec, profile=profile)


def mark_for_deletion(opts, cluster_id, profile=None):
    """Mark a cluster for deletion (preflight; pair with delete)."""
    return update(opts, cluster_id, {"markForDeletion": True}, profile=profile)
