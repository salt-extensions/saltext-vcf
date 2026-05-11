"""VCF Operations — policies and notification rules."""

import requests

from saltext.vmware.utils import vcfops

_POLICIES = "/suite-api/api/policies"
_NOTIFICATIONS = "/suite-api/api/notifications/rules"


def list_(opts):
    return vcfops.api_get(opts, _POLICIES)


def get(opts, policy_id):
    return vcfops.api_get(opts, f"{_POLICIES}/{policy_id}")


def get_or_none(opts, policy_id):
    try:
        return get(opts, policy_id)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def notification_rules_list(opts):
    return vcfops.api_get(opts, _NOTIFICATIONS)
