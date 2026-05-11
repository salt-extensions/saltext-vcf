"""VCF Operations — report instances.

Report *definitions* live under ``/suite-api/api/reports/definitions``
but that path returns 400 without a query filter; the practical access
pattern is to list known instances (``GET /reports``) and generate new
ones (``POST /reports``).
"""

import requests

from saltext.vmware.utils import vcfops

_PATH = "/suite-api/api/reports"


def list_(opts, page=0, page_size=1000):
    return vcfops.api_get(opts, _PATH, params={"page": page, "pageSize": page_size})


def get(opts, report_id):
    return vcfops.api_get(opts, f"{_PATH}/{report_id}")


def get_or_none(opts, report_id):
    try:
        return get(opts, report_id)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def generate(opts, report_spec):
    """Trigger a report generation.

    *report_spec* example::

        {"resourceId": "<uuid>", "reportDefinitionId": "<uuid>"}
    """
    return vcfops.api_post(opts, _PATH, body=report_spec)


def download(opts, report_id, fmt="PDF"):
    """Stream a generated report. Returns raw bytes — caller writes to disk."""
    session, host = vcfops._session(opts)
    resp = session.get(
        f"https://{host}{_PATH}/{report_id}/download",
        params={"format": fmt},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.content


def delete(opts, report_id):
    return vcfops.api_delete(opts, f"{_PATH}/{report_id}")
