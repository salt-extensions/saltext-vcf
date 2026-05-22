"""VCF Operations — truststore certificates.

VCF Operations 9.x exposes its trusted-certificate store at
``/suite-api/api/certificate``. Three operations are supported:

* ``GET    /suite-api/api/certificate``                       — list all certs
* ``POST   /suite-api/api/certificate``                       — import (multipart)
* ``DELETE /suite-api/api/certificate?thumbprint=…&force=…``  — delete one

Each certificate object carries ``thumbprint`` (SHA-1 fingerprint),
``certificateDetails`` (issuer + expiration string), ``issuedTo`` /
``issuedBy`` (subject + issuer DN).
"""

from saltext.vcf.utils import vcfops

_CERT = "/suite-api/api/certificate"


def list_(opts, profile=None):
    """Return every certificate currently in the VCF Operations truststore.

    Each entry: ``{"thumbprint": ..., "certificateDetails": ..., "issuedTo":
    ..., "issuedBy": ...}``.
    """
    resp = vcfops.api_get(opts, _CERT, profile=profile)
    return resp.get("certificates", []) or []


def get(opts, thumbprint, profile=None):
    """Return the certificate whose SHA-1 thumbprint matches *thumbprint*.

    Raises ``KeyError`` if no certificate with that thumbprint is currently
    in the truststore. Use :func:`get_or_none` for the idempotent variant.
    """
    for cert in list_(opts, profile=profile):
        if cert.get("thumbprint") == thumbprint:
            return cert
    raise KeyError(f"certificate {thumbprint!r} not found in truststore")


def get_or_none(opts, thumbprint, profile=None):
    try:
        return get(opts, thumbprint, profile=profile)
    except KeyError:
        return None


def delete(opts, thumbprint, *, force=False, profile=None):
    """Delete a certificate by thumbprint.

    *force* tells VCF Operations to delete even if active adapters
    reference it. Default ``False`` is the safe choice.
    """
    params = {"thumbprint": thumbprint, "force": "true" if force else "false"}
    return vcfops.api_delete(opts, _CERT, params=params, profile=profile)
