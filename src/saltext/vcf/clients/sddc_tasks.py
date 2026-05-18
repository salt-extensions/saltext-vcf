"""SDDC Manager async task polling.

Most VCF lifecycle operations (create domain, expand cluster, deploy
edge, etc.) return ``202 Accepted`` with a task identifier. This module
provides the read + poll loop those callers need.

Task statuses observed in VCF 9.x:
- ``IN_PROGRESS``
- ``Pending``
- ``Successful``
- ``Failed``
- ``Cancelled``
"""

import time

import requests

from saltext.vcf.utils import sddc

PATH = "/v1/tasks"
TERMINAL = {"Successful", "Failed", "Cancelled"}


def list_(opts, page=0, page_size=100, profile=None):
    return sddc.api_get(opts, PATH, params={"page": page, "pageSize": page_size}, profile=profile)


def get(opts, task_id, profile=None):
    return sddc.api_get(opts, f"{PATH}/{task_id}", profile=profile)


def get_or_none(opts, task_id, profile=None):
    try:
        return get(opts, task_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def retry(opts, task_id, profile=None):
    """Retry a failed task. Returns the task body."""
    return sddc.api_patch(opts, f"{PATH}/{task_id}", body={}, profile=profile)


def cancel(opts, task_id, profile=None):
    return sddc.api_delete(opts, f"{PATH}/{task_id}", profile=profile)


def wait(
    opts,
    task_id,
    *,
    timeout=3600,
    poll_interval=10,
    profile=None,
):
    """Block until *task_id* reaches a terminal status. Returns the final task body.

    Raises :class:`TimeoutError` if the task does not finish within
    *timeout* seconds. Raises :class:`RuntimeError` on terminal
    ``Failed`` / ``Cancelled``.
    """
    deadline = time.monotonic() + float(timeout)
    while True:
        task = get(opts, task_id, profile=profile)
        status = task.get("status")
        if status in TERMINAL:
            if status != "Successful":
                msg = _error_message(task)
                raise RuntimeError(f"task {task_id} ended with status {status!r}: {msg}")
            return task
        if time.monotonic() >= deadline:
            raise TimeoutError(f"task {task_id} still {status!r} after {timeout}s")
        time.sleep(float(poll_interval))


def _error_message(task):
    errors = task.get("errors") or []
    if errors:
        msgs = []
        for e in errors:
            if isinstance(e, dict):
                msgs.append(e.get("message") or e.get("errorCode") or repr(e))
            else:
                msgs.append(str(e))
        return "; ".join(msgs)
    return task.get("status_message") or task.get("description") or ""
