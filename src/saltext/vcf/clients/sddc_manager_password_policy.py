"""Password policy client for SDDC Manager (appliancemanager API over SSH).

Remote equivalent of the ``mops`` config-modules password-age control
(configuration id 1620). The policy lives behind the appliance-local,
unauthenticated endpoint
``http://localhost/appliancemanager/security/password-policy`` — the same
endpoint the on-appliance controller uses (see
``framework/clients/sddc_manager/sddc_manager_consts.py:LOCAL_PASSWORD_POLICY_URL``).
There is **no remote SDDC Manager REST equivalent** (the
``/v1/users/local-accounts/password-policy`` path is not present on VCF 9.x),
so this client runs ``curl`` against ``localhost`` on the appliance over SSH.

The appliancemanager API uses ``maximumPasswordAge``; this client exposes it as
``passwordExpirationDays`` (the config-modules schema name used by the
``vcf_sddc_manager_password_policy`` state) and translates back on write, while
passing the remaining native fields (``minimumLength``,
``minimumUpperCaseLetters``, ``passwordHistory``, ``maximumAuthenticationFailures``,
``failInterval``, ``unlockTime`` …) through unchanged.

SSH config is read from ``saltext.vcf.sddc_manager.ssh`` (see
:mod:`saltext.vcf.clients.sddc_manager_local_accounts`).
"""

import json
import logging
import shlex

from saltext.vcf.utils import sddc
from saltext.vcf.utils import ssh as ssh_util

log = logging.getLogger(__name__)

# Appliance-local appliancemanager endpoint (unauthenticated, localhost only).
LOCAL_PASSWORD_POLICY_URL = "http://localhost/appliancemanager/security/password-policy"

# API field <-> schema field for the password-age control.
_API_AGE_FIELD = "maximumPasswordAge"
_SCHEMA_AGE_FIELD = "passwordExpirationDays"


def _to_policy(api):
    """Expose the appliancemanager API dict with a schema-friendly age alias.

    Adds ``passwordExpirationDays`` (= API ``maximumPasswordAge``) so callers
    and the ``vcf_sddc_manager_password_policy`` state can use the
    config-modules schema name; native fields are preserved.
    """
    policy = dict(api)
    if _API_AGE_FIELD in api:
        policy[_SCHEMA_AGE_FIELD] = api.get(_API_AGE_FIELD)
    return policy


def _to_api_payload(body):
    """Translate a policy dict (schema-side) back to the appliancemanager shape.

    Maps ``passwordExpirationDays`` -> ``maximumPasswordAge`` and drops the
    schema-only alias so the PUT body matches the native API.
    """
    payload = {k: v for k, v in body.items() if k != _SCHEMA_AGE_FIELD}
    if _SCHEMA_AGE_FIELD in body:
        payload[_API_AGE_FIELD] = body[_SCHEMA_AGE_FIELD]
    return payload


def get(opts, profile=None):
    """Return the current local-account password policy from SDDC Manager.

    :param opts: Salt opts / pillar dict.
    :param profile: Optional named profile key.
    :return: Policy dict exposing ``passwordExpirationDays`` plus native fields.
    :raises RuntimeError: if the policy cannot be read over SSH.
    """
    ssh_cfg = sddc.get_ssh_config(opts, profile=profile)
    cmd = f"curl -sf -H 'Content-Type: application/json' {LOCAL_PASSWORD_POLICY_URL}"
    rc, out, err = ssh_util.run(ssh_cfg, cmd)
    if rc != 0:
        raise RuntimeError(
            f"Failed to GET password policy on {ssh_cfg.get('host')}: rc={rc} {err.strip()}"
        )
    return _to_policy(json.loads(out))


def set_(opts, body, profile=None):
    """Update the local-account password policy via the appliancemanager API.

    :param opts: Salt opts / pillar dict.
    :param body: Policy dict (schema-side; ``passwordExpirationDays`` accepted).
    :param profile: Optional named profile key.
    :return: Updated policy dict (same shape as :func:`get`).
    :raises RuntimeError: if the update fails over SSH.
    """
    ssh_cfg = sddc.get_ssh_config(opts, profile=profile)
    data = json.dumps(_to_api_payload(body))
    cmd = (
        "curl -sf -X PUT -H 'Content-Type: application/json' "
        f"-d {shlex.quote(data)} {LOCAL_PASSWORD_POLICY_URL}"
    )
    rc, out, err = ssh_util.run(ssh_cfg, cmd)
    if rc != 0:
        raise RuntimeError(
            f"Failed to PUT password policy on {ssh_cfg.get('host')}: rc={rc} {err.strip()}"
        )
    return _to_policy(json.loads(out)) if out.strip() else {}
