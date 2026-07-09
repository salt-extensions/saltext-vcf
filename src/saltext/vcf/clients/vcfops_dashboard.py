"""VCF Operations — dashboards.

VCF Operations exposes dashboard management at ``/suite-api/api/dashboards``.
A dashboard is a named collection of widgets scoped to a user or shared with
other users. The API supports the usual CRUD lifecycle plus two extras:

* ``POST /suite-api/api/dashboards/{id}/share/{userId}`` — grant *userId*
  access to the dashboard.
* ``POST /suite-api/api/dashboards/import`` — recreate a dashboard from a
  previously exported payload (typically produced by the export endpoint or
  captured out-of-band).

All requests are token-authenticated via :mod:`saltext.vcf.utils.vcfops`.
"""

import requests

from saltext.vcf.utils import vcfops

_DASH = "/suite-api/api/dashboards"


def list_(opts, profile=None):
    """Return every dashboard visible to the current user."""
    return vcfops.api_get(opts, _DASH, profile=profile)


def get(opts, dashboard_id, profile=None):
    """Return the dashboard identified by *dashboard_id*.

    Raises :class:`requests.HTTPError` (404) if the dashboard is missing;
    use :func:`get_or_none` for the idempotent variant.
    """
    return vcfops.api_get(opts, f"{_DASH}/{dashboard_id}", profile=profile)


def get_or_none(opts, dashboard_id, profile=None):
    """Like :func:`get` but returns ``None`` when the dashboard is absent."""
    try:
        return get(opts, dashboard_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, dashboard_spec, profile=None):
    """Create a dashboard.

    *dashboard_spec* is the JSON body accepted by
    ``POST /suite-api/api/dashboards``. Example::

        {
            "name": "capacity-overview",
            "description": "Cluster-level capacity trends",
            "widgets": [...]
        }
    """
    return vcfops.api_post(opts, _DASH, body=dashboard_spec, profile=profile)


def update(opts, dashboard_id, dashboard_spec, profile=None):
    """Replace the dashboard identified by *dashboard_id* with *dashboard_spec*."""
    return vcfops.api_put(opts, f"{_DASH}/{dashboard_id}", body=dashboard_spec, profile=profile)


def delete(opts, dashboard_id, profile=None):
    """Delete the dashboard identified by *dashboard_id*."""
    return vcfops.api_delete(opts, f"{_DASH}/{dashboard_id}", profile=profile)


def share(opts, dashboard_id, user_id, profile=None):
    """Share *dashboard_id* with the user identified by *user_id*."""
    return vcfops.api_post(opts, f"{_DASH}/{dashboard_id}/share/{user_id}", profile=profile)


def import_(opts, spec, profile=None):
    """Import a dashboard from a previously exported payload.

    *spec* is the exported dashboard JSON structure accepted by
    ``POST /suite-api/api/dashboards/import``.
    """
    return vcfops.api_post(opts, f"{_DASH}/import", body=spec, profile=profile)
