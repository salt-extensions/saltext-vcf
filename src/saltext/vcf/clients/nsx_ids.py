"""NSX Distributed IDS/IPS — settings, profiles, signature management, policies, rules.

Surfaces:

- Global cluster config (``/policy/api/v1/infra/settings/firewall/security/intrusion-services``).
- Per-cluster enablement (``.../cluster-configs/{cluster_id}``).
- Profiles (``.../profiles``).
- Signature management (``.../signatures``).
- IDS policies + rules (``/infra/domains/{d}/intrusion-service-policies/...``).
"""

import requests

from saltext.vcf.utils import nsx

GLOBAL_CONFIG = "/policy/api/v1/infra/settings/firewall/security/intrusion-services"
CLUSTER_CONFIGS = f"{GLOBAL_CONFIG}/cluster-configs"
PROFILES = f"{GLOBAL_CONFIG}/profiles"
SIGNATURE_VERSIONS = f"{GLOBAL_CONFIG}/signature-versions"


def _signatures_path(version="DEFAULT"):
    """Signatures live under a signature-version (NSX 9+ surfaces). ``DEFAULT``
    is the currently-active version maintained by NSX."""
    return f"{SIGNATURE_VERSIONS}/{version}/signatures"


def _policy_path(domain, policy=None):
    base = f"/policy/api/v1/infra/domains/{domain}/intrusion-service-policies"
    return f"{base}/{policy}" if policy else base


def _rule_path(domain, policy, rule=None):
    base = f"/policy/api/v1/infra/domains/{domain}/intrusion-service-policies/{policy}/rules"
    return f"{base}/{rule}" if rule else base


# Global config


def get_global_config(opts, profile=None):
    return nsx.api_get(opts, GLOBAL_CONFIG, profile=profile)


def set_global_config(opts, profile=None, **spec):
    body = {"resource_type": spec.pop("resource_type", "IdsGlobalConfig")}
    body.update(spec)
    return nsx.api_put(opts, GLOBAL_CONFIG, body=body, profile=profile)


# Per-cluster configs


def list_cluster_configs(opts, profile=None):
    return nsx.api_get(opts, CLUSTER_CONFIGS, profile=profile)


def get_cluster_config(opts, cluster_id, profile=None):
    return nsx.api_get(opts, f"{CLUSTER_CONFIGS}/{cluster_id}", profile=profile)


def get_cluster_config_or_none(opts, cluster_id, profile=None):
    try:
        return get_cluster_config(opts, cluster_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def set_cluster_config(opts, cluster_id, profile=None, **spec):
    body = {"resource_type": spec.pop("resource_type", "IdsClusterConfig")}
    body.update(spec)
    return nsx.api_put(opts, f"{CLUSTER_CONFIGS}/{cluster_id}", body=body, profile=profile)


# Profiles


def list_profiles(opts, profile=None):
    return nsx.api_get(opts, PROFILES, profile=profile)


def get_profile(opts, profile_id, profile=None):
    return nsx.api_get(opts, f"{PROFILES}/{profile_id}", profile=profile)


def get_profile_or_none(opts, profile_id, profile=None):
    try:
        return get_profile(opts, profile_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create_profile(opts, profile_id, profile=None, **spec):
    body = {
        "resource_type": spec.pop("resource_type", "IdsProfile"),
        "display_name": spec.pop("display_name", profile_id),
    }
    body.update(spec)
    return nsx.api_put(opts, f"{PROFILES}/{profile_id}", body=body, profile=profile)


def delete_profile(opts, profile_id, profile=None):
    return nsx.api_delete(opts, f"{PROFILES}/{profile_id}", profile=profile)


# Signatures (read-only catalog managed by NSX)


def list_signatures(opts, version="DEFAULT", profile=None):
    return nsx.api_get(opts, _signatures_path(version), profile=profile)


def get_signature(opts, signature_id, version="DEFAULT", profile=None):
    return nsx.api_get(opts, f"{_signatures_path(version)}/{signature_id}", profile=profile)


# IDS policies (per-domain)


def list_policies(opts, domain="default", profile=None):
    return nsx.api_get(opts, _policy_path(domain), profile=profile)


def get_policy(opts, policy, domain="default", profile=None):
    return nsx.api_get(opts, _policy_path(domain, policy), profile=profile)


def get_policy_or_none(opts, policy, domain="default", profile=None):
    try:
        return get_policy(opts, policy, domain=domain, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create_policy(opts, policy, domain="default", profile=None, **spec):
    body = {"display_name": spec.pop("display_name", policy)}
    body.update(spec)
    return nsx.api_put(opts, _policy_path(domain, policy), body=body, profile=profile)


def delete_policy(opts, policy, domain="default", profile=None):
    return nsx.api_delete(opts, _policy_path(domain, policy), profile=profile)


# IDS rules (per-policy)


def list_rules(opts, policy, domain="default", profile=None):
    return nsx.api_get(opts, _rule_path(domain, policy), profile=profile)


def get_rule(opts, rule, policy, domain="default", profile=None):
    return nsx.api_get(opts, _rule_path(domain, policy, rule), profile=profile)


def get_rule_or_none(opts, rule, policy, domain="default", profile=None):
    try:
        return get_rule(opts, rule, policy, domain=domain, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create_rule(opts, rule, policy, domain="default", profile=None, **spec):
    body = {"display_name": spec.pop("display_name", rule)}
    body.update(spec)
    return nsx.api_put(opts, _rule_path(domain, policy, rule), body=body, profile=profile)


def delete_rule(opts, rule, policy, domain="default", profile=None):
    return nsx.api_delete(opts, _rule_path(domain, policy, rule), profile=profile)
