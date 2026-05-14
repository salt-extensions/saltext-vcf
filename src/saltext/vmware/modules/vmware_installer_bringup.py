"""Execution module for VCF Installer bringup (validate + submit + poll)."""

from saltext.vmware.clients import installer_bringup as c

__virtualname__ = "vmware_installer_bringup"


def __virtual__():
    return __virtualname__


def validate(spec, profile=None):
    """Submit a bringup spec for validation. Returns ``{id, executionStatus, ...}``.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_installer_bringup.validate "$(cat /tmp/spec.json)"
    """
    return c.validate(__opts__, spec, profile=profile)


def validation_status(validation_id, profile=None):
    """Return current state of a validation.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_installer_bringup.validation_status <validation_id>
    """
    return c.validation_status(__opts__, validation_id, profile=profile)


def list_validations(profile=None):
    """List all validations.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_installer_bringup.list_validations
    """
    return c.list_validations(__opts__, profile=profile)


def wait_validation(validation_id, timeout=1800, poll_interval=10, profile=None):
    """Block until validation terminates. Default timeout 30 minutes.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_installer_bringup.wait_validation <validation_id>
    """
    return c.wait_validation(
        __opts__, validation_id, timeout=timeout, poll_interval=poll_interval, profile=profile
    )


def submit(spec, profile=None):
    """Submit a validated bringup spec. Returns the task dict.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_installer_bringup.submit "$(cat /tmp/spec.json)"
    """
    return c.submit(__opts__, spec, profile=profile)


def status(sddc_id, profile=None):
    """Return current bringup task state.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_installer_bringup.status <sddc_id>
    """
    return c.status(__opts__, sddc_id, profile=profile)


def list_(profile=None):
    """List all bringup tasks.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_installer_bringup.list_
    """
    return c.list_(__opts__, profile=profile)


def retry(sddc_id, profile=None):
    """Retry a failed bringup at the failed step.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_installer_bringup.retry <sddc_id>
    """
    return c.retry(__opts__, sddc_id, profile=profile)


def wait(sddc_id, timeout=14400, poll_interval=60, profile=None):
    """Block until bringup terminates. Default timeout 4 hours.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_installer_bringup.wait <sddc_id>
    """
    return c.wait(__opts__, sddc_id, timeout=timeout, poll_interval=poll_interval, profile=profile)
