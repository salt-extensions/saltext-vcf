"""VCF Automation — vRO configuration elements (``/vco/api/configurations``).

Configuration elements are vRO's named, typed key-value bundles —
the canonical place to stash environment-specific tunables that
workflows reference.
"""

import requests

from saltext.vcf.utils import vcfa

_BASE = "/vco/api/configurations"


def list_(opts, category=None, profile=None):
    params = {"categoryId": category} if category else None
    resp = vcfa.api_get(opts, _BASE, params=params, profile=profile)
    return resp.get("link", []) or resp.get("content", []) or []


def get(opts, config_id, profile=None):
    return vcfa.api_get(opts, f"{_BASE}/{config_id}", profile=profile)


def get_or_none(opts, config_id, profile=None):
    try:
        return get(opts, config_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def create(opts, spec, profile=None):
    """Create a configuration element.

    *spec* keys: ``name``, ``description``, ``categoryId``, ``attributes``
    (list of ``{name, type, description, value}``), ``version``.
    """
    return vcfa.api_post(opts, _BASE, body=spec, profile=profile)


def update(opts, config_id, spec, profile=None):
    return vcfa.api_put(opts, f"{_BASE}/{config_id}", body=spec, profile=profile)


def delete(opts, config_id, profile=None):
    return vcfa.api_delete(opts, f"{_BASE}/{config_id}", profile=profile)


def get_attribute(opts, config_id, attribute_name, profile=None):
    return vcfa.api_get(opts, f"{_BASE}/{config_id}/attributes/{attribute_name}", profile=profile)


def set_attribute(opts, config_id, attribute_name, attribute_spec, profile=None):
    """Set a single attribute. *attribute_spec* is ``{name, type, value}``."""
    return vcfa.api_put(
        opts,
        f"{_BASE}/{config_id}/attributes/{attribute_name}",
        body=attribute_spec,
        profile=profile,
    )
