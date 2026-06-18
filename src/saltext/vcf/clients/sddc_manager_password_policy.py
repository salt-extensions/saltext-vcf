"""Password policy client for SDDC Manager (/v1/users/local-accounts/password-policy).

Reads and writes the local account password expiration policy via the
authenticated SDDC Manager REST API.  This is the remote equivalent of the
``http://localhost/appliancemanager/security/password-policy`` endpoint used
inside the appliance — the remote API requires Bearer token auth (handled by
:mod:`saltext.vcf.utils.sddc`).

Config is read from Salt opts/pillar under ``saltext.vcf.sddc_manager``:

.. code-block:: yaml

    saltext.vcf:
      sddc_manager:
        host: sddc-manager.example.test
        username: administrator@vsphere.local
        password: secret
        verify_ssl: false
"""

from saltext.vcf.utils import sddc

_PATH = "/v1/users/local-accounts/password-policy"


def get(opts, profile=None):
    """Return the current local-account password policy.

    :param opts: Salt opts / pillar dict.
    :param profile: Optional named profile key.
    :return: Password policy dict (keys include ``passwordExpirationDays``,
        ``minimumLength``, ``maximumAuthenticationFailures``, etc.)
    """
    return sddc.api_get(opts, _PATH, profile=profile)


def set_(opts, body, profile=None):
    """Update the local-account password policy.

    :param opts: Salt opts / pillar dict.
    :param body: Dict of policy fields to update (same schema as ``get``).
    :param profile: Optional named profile key.
    :return: Updated policy dict.
    """
    return sddc.api_put(opts, _PATH, body=body, profile=profile)
