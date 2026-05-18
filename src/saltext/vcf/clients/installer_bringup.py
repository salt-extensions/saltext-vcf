"""VCF Installer bringup — validate spec, submit, poll progress.

The bringup spec is a sizable JSON document describing the target management
domain: ESXi hosts, network pools, DNS/NTP, vCenter spec, NSX spec, vSAN
config, and credentials. The standard workflow is::

    spec = {...}
    val_id = installer_bringup.validate(opts, spec)["id"]
    while True:
        v = installer_bringup.validation_status(opts, val_id)
        if v["executionStatus"] != "IN_PROGRESS":
            break
    if v["resultStatus"] != "SUCCEEDED":
        raise RuntimeError(v)
    sddc = installer_bringup.submit(opts, spec)
    sddc_id = sddc["id"]
    # Poll for ~hours...
    while installer_bringup.status(opts, sddc_id)["status"] == "IN_PROGRESS":
        time.sleep(60)
"""

import time

import requests

from saltext.vcf.utils import installer

# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------


def validate(opts, spec, profile=None):
    """Submit a bringup spec for validation. Returns ``{id, executionStatus, ...}``.

    Validation is asynchronous; poll with :func:`validation_status`.
    """
    return installer.api_post(opts, "/v1/sddcs/validations", body=spec, profile=profile)


def validation_status(opts, validation_id, profile=None):
    """Return the current state of a validation."""
    return installer.api_get(opts, f"/v1/sddcs/validations/{validation_id}", profile=profile)


def validation_status_or_none(opts, validation_id, profile=None):
    try:
        return validation_status(opts, validation_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def list_validations(opts, profile=None):
    """Return all known validations."""
    return installer.api_get(opts, "/v1/sddcs/validations", profile=profile)


def wait_validation(opts, validation_id, *, timeout=1800, poll_interval=10, profile=None):
    """Block until *validation_id* terminates. Returns the final dict.

    Raises ``TimeoutError`` after *timeout* seconds; raises ``RuntimeError`` if
    the validation finishes with a non-success ``resultStatus``.
    """
    deadline = time.monotonic() + float(timeout)
    while True:
        info = validation_status(opts, validation_id, profile=profile)
        exec_state = info.get("executionStatus") or info.get("status")
        if exec_state not in ("IN_PROGRESS", "PENDING", "QUEUED"):
            result = info.get("resultStatus") or info.get("status")
            if result not in ("SUCCEEDED", "COMPLETED", "PASSED"):
                raise RuntimeError(f"validation {validation_id} ended {result!r}: {info}")
            return info
        if time.monotonic() >= deadline:
            raise TimeoutError(f"validation {validation_id} did not complete in {timeout}s")
        time.sleep(float(poll_interval))


# --------------------------------------------------------------------------
# Submit + poll
# --------------------------------------------------------------------------


def submit(opts, spec, profile=None):
    """Submit a validated bringup spec. Returns ``{id, status, ...}``.

    Bringup runs for ~hours. Poll with :func:`status` or use :func:`wait`.
    """
    return installer.api_post(opts, "/v1/sddcs", body=spec, profile=profile)


def status(opts, sddc_id, profile=None):
    """Return current bringup task state."""
    return installer.api_get(opts, f"/v1/sddcs/{sddc_id}", profile=profile)


def status_or_none(opts, sddc_id, profile=None):
    try:
        return status(opts, sddc_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def list_(opts, profile=None):
    """Return all known bringup tasks (current + historical)."""
    return installer.api_get(opts, "/v1/sddcs", profile=profile)


def retry(opts, sddc_id, profile=None):
    """Retry a failed bringup at the failed step. Returns the task dict."""
    return installer.api_patch(
        opts, f"/v1/sddcs/{sddc_id}", body={"action": "RETRY"}, profile=profile
    )


def wait(opts, sddc_id, *, timeout=14400, poll_interval=60, profile=None):
    """Block until bringup terminates. Default timeout is 4 hours.

    Returns the final task dict. Raises ``RuntimeError`` on failure,
    ``TimeoutError`` if the deadline is hit.
    """
    deadline = time.monotonic() + float(timeout)
    while True:
        info = status(opts, sddc_id, profile=profile)
        state = info.get("status")
        if state not in ("IN_PROGRESS", "PENDING", "QUEUED"):
            if state not in ("COMPLETED_WITH_SUCCESS", "SUCCEEDED", "COMPLETED"):
                raise RuntimeError(f"bringup {sddc_id} ended {state!r}: {info}")
            return info
        if time.monotonic() >= deadline:
            raise TimeoutError(f"bringup {sddc_id} did not complete in {timeout}s")
        time.sleep(float(poll_interval))
