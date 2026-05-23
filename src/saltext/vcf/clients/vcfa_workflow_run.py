"""VCF Automation — vRO workflow executions (``/vco/api/workflows/{wfId}/executions``).

A *run* is a single invocation of a workflow. The execution surface
supports start / get / cancel / log retrieval, all scoped under the
parent workflow id.
"""

import requests

from saltext.vcf.utils import vcfa

_WORKFLOWS = "/vco/api/workflows"


def list_(opts, workflow_id, profile=None):
    """List executions of a workflow."""
    resp = vcfa.api_get(opts, f"{_WORKFLOWS}/{workflow_id}/executions", profile=profile)
    return resp.get("relations", {}).get("link", []) or resp.get("content", []) or []


def get(opts, workflow_id, run_id, profile=None):
    return vcfa.api_get(opts, f"{_WORKFLOWS}/{workflow_id}/executions/{run_id}", profile=profile)


def get_or_none(opts, workflow_id, run_id, profile=None):
    try:
        return get(opts, workflow_id, run_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def start(opts, workflow_id, parameters=None, profile=None):
    """Start a workflow execution.

    *parameters* is the vRO input-parameter list: each entry is
    ``{name, type, value}``. Returns the execution metadata; poll via
    :func:`get` for completion.
    """
    body = {"parameters": list(parameters)} if parameters else {}
    return vcfa.api_post(opts, f"{_WORKFLOWS}/{workflow_id}/executions", body=body, profile=profile)


def cancel(opts, workflow_id, run_id, profile=None):
    """Cancel a running execution."""
    return vcfa.api_post(
        opts,
        f"{_WORKFLOWS}/{workflow_id}/executions/{run_id}/state",
        body={"value": "canceled"},
        profile=profile,
    )


def logs(opts, workflow_id, run_id, profile=None):
    return vcfa.api_get(
        opts, f"{_WORKFLOWS}/{workflow_id}/executions/{run_id}/logs", profile=profile
    )


def state(opts, workflow_id, run_id, profile=None):
    """Return just the ``state`` field of an execution.

    Handy for polling loops without round-tripping the full body.
    """
    return vcfa.api_get(
        opts, f"{_WORKFLOWS}/{workflow_id}/executions/{run_id}/state", profile=profile
    )
