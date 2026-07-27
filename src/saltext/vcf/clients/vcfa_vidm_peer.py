"""VCF Automation — vRA → vIDM peer trust (TLS certificate).

VCF Automation retains the Aria Automation 8.x federation with a
VMware Identity Manager (vIDM) tenant. The 912-controls gap requires
that the vRA-side reference to vIDM present a valid TLS peer
certificate — i.e. the CA / leaf trust store the appliance uses when
it calls out to vIDM's ``/SAAS`` endpoints must be replaced whenever
vIDM's certificate is rotated.

Endpoints (Aria Automation internal API, still present on VCFA
appliances)::

    GET  /provisioning/mgmt/identity-vidm-peer            — current config
    PUT  /provisioning/mgmt/identity-vidm-peer            — replace config
    POST /provisioning/mgmt/identity-vidm-peer/validate   — dry-run test

Fields of interest:

* ``hostAddress`` — vIDM host (e.g. ``vidm.example.com``)
* ``clientId`` / ``clientSecret`` — OAuth client
* ``peerCertificate`` — PEM-encoded trust anchor (this is what the
  hardening gap targets)

The helpers here are cert-focused; :func:`vidm_peer_get` returns the
raw config dict and :func:`vidm_peer_set` PUTs a merge of the current
config with the supplied fields.
"""

import requests

from saltext.vcf.utils import vcfa

_VIDM = "/provisioning/mgmt/identity-vidm-peer"


def vidm_peer_get(opts, *, profile=None):
    """Return the current vIDM peer config, or ``None`` on 404."""
    try:
        return vcfa.api_get(opts, _VIDM, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def vidm_peer_set(opts, *, cert=None, host=None, client_id=None, client_secret=None, profile=None):
    """PUT vIDM peer config, merging over the existing values.

    Only fields you name are overwritten. *cert* replaces the peer
    trust certificate (PEM). Raises ``ValueError`` if nothing is
    supplied.
    """
    if cert is None and host is None and client_id is None and client_secret is None:
        raise ValueError(
            "vidm_peer_set: at least one of cert, host, client_id, client_secret is required"
        )
    current = vidm_peer_get(opts, profile=profile) or {}
    body = dict(current)
    if cert is not None:
        body["peerCertificate"] = cert
    if host is not None:
        body["hostAddress"] = host
    if client_id is not None:
        body["clientId"] = client_id
    if client_secret is not None:
        body["clientSecret"] = client_secret
    return vcfa.api_put(opts, _VIDM, body=body, profile=profile)


def vidm_peer_validate(opts, spec, *, profile=None):
    """POST a candidate config to the validate endpoint (dry run)."""
    return vcfa.api_post(opts, f"{_VIDM}/validate", body=spec, profile=profile)
