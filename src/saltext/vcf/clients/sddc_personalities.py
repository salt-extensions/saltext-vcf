"""SDDC Manager cluster personalities (/v1/personalities).

A *personality* is a captured vSphere Lifecycle Manager cluster image
(base image + add-ons + components + firmware) that SDDC Manager can
reuse as a standard baseline when creating or upgrading clusters. The
Async Patch Tool workflow can produce a personality from a patched
cluster and register it here so subsequent clusters get the same image.
"""

import requests

from saltext.vcf.utils import sddc

PATH = "/v1/personalities"


def list_(opts, personality_name=None, cluster_id=None, profile=None):
    """List personalities, optionally filtered by name or seed cluster id."""
    params = {}
    if personality_name is not None:
        params["personalityName"] = personality_name
    if cluster_id is not None:
        params["clusterId"] = cluster_id
    return sddc.api_get(opts, PATH, params=params or None, profile=profile)


def get(opts, personality_id, profile=None):
    return sddc.api_get(opts, f"{PATH}/{personality_id}", profile=profile)


def get_or_none(opts, personality_id, profile=None):
    try:
        return get(opts, personality_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, personality_spec, profile=None):
    """Import a new personality. *personality_spec* per SDDC Manager API."""
    return sddc.api_post(opts, PATH, body=personality_spec, profile=profile)


def delete(opts, personality_id, profile=None):
    """Delete a personality by id."""
    return sddc.api_delete(opts, f"{PATH}/{personality_id}", profile=profile)


def rename(opts, personality_id, personality_name, profile=None):
    """Rename a personality."""
    return sddc.api_patch(
        opts,
        f"{PATH}/{personality_id}",
        body={"personalityName": personality_name},
        profile=profile,
    )


def upload_files(opts, upload_spec, profile=None):
    """Upload the raw ZIP/JSON files that back a personality.

    *upload_spec* is the ``PersonalityUploadSpec`` body per SDDC Manager API
    (e.g. ``{"filePath": "/nfs/.../personality.zip", "personalityName":
    "cluster-image-8.0u3"}``). The two-step flow is: upload files first,
    then call :func:`create` referencing the uploaded file id.
    """
    return sddc.api_put(opts, f"{PATH}/files", body=upload_spec, profile=profile)
