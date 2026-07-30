"""VCF Operations for Logs (vRLI) — appliance certificate lifecycle.

vRLI exposes its appliance certificate at ``/api/v2/certificate``
(singular — the plural ``/api/v2/certificates`` used by earlier vRLI
releases returns 404 on the 9.0.2.0 build we probed live).

Verbs discovered live::

    GET  /api/v2/certificate       -> [ { owner: {...}, issuer: {...},
                                          serialNum: "...",
                                          validityPeriod: {from, until} } ]

    POST /api/v2/certificate       {"certificate": "<PEM cert + key>"}
        -> replaces the appliance cert; restarts the API listener

The ``certificate`` field must contain both the leaf certificate and
its private key concatenated in PEM form; an optional intermediate
chain is appended between them. The API service **restarts** after a
successful POST — callers should expect the next request to timeout
briefly. No DELETE handler exists (returns 404 for DELETE).
"""

from saltext.vcf.utils import vrli

_CERT = "/api/v2/certificate"


def list_(opts, profile=None):
    """Return every certificate currently installed on the appliance.

    Each entry: ``{"owner": {commonName, organization, ...}, "issuer":
    {...}, "serialNum": "...", "validityPeriod": {"from": ..., "until":
    ...}}``. The list is normally length-1 (the appliance's own leaf).
    """
    resp = vrli.api_get(opts, _CERT, profile=profile)
    if isinstance(resp, list):
        return resp
    return resp.get("certificates", []) or []


def get(opts, profile=None):
    """Return the first (typically only) certificate, or ``None`` if none."""
    entries = list_(opts, profile=profile)
    return entries[0] if entries else None


def install(opts, cert_pem, key_pem, chain_pem=None, profile=None):
    """Install a replacement appliance certificate.

    *cert_pem*  — the leaf certificate in PEM form.
    *key_pem*   — its private key in PEM form (unencrypted).
    *chain_pem* — optional intermediate chain in PEM form (concatenated
    between the leaf and the key).

    Note: this operation **restarts the appliance API listener**.
    The next REST call will typically time out for 30-90 s.
    """
    parts = [cert_pem.strip(), "\n"]
    if chain_pem:
        parts.extend([chain_pem.strip(), "\n"])
    parts.extend([key_pem.strip(), "\n"])
    combined = "".join(parts)
    body = {"certificate": combined}
    return vrli.api_post(opts, _CERT, body=body, profile=profile)


def serial_number(opts, profile=None):
    """Return the hex ``serialNum`` of the installed cert, or ``None``."""
    cert = get(opts, profile=profile)
    return cert.get("serialNum") if cert else None
