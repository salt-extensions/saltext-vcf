"""VCF Operations — fleet certificate management (VCF 9.x).

The VCF Operations 9.1 ``suite-api`` exposes a fleet-wide certificate manager
at ``/suite-api/api/fleet-management/certificate-management``. Each managed
**certificate** is identified by an opaque ``certificateResourceKey``; query
results include expiration metadata (``expiryDate`` as a unix-millisecond
timestamp, ``daysToExpire`` as an int, ``status``:
``NORMAL`` / ``EXPIRING`` / ``EXPIRED`` / ``UNKNOWN``).

Endpoints used here (all on the VCF Operations host):

* ``POST   /suite-api/api/fleet-management/certificate-management/certificates/query``
  — paginated list, with optional ``appliance`` / ``applianceFqdn`` /
  ``status`` / ``category`` filters; query params ``page``, ``pageSize``.
* ``GET    /suite-api/api/fleet-management/certificate-management/certificates/{certificateId}``
  — fetch a single certificate record by its ``certificateResourceKey``.
* ``PUT    /suite-api/api/fleet-management/certificate-management/certificates/{certificateId}``
  — replace the certificate; for a custom external CA pass
  ``ca_type="EXTERNAL_CA"`` plus a PEM ``certificate_chain``; for the
  integrated Microsoft CA pass ``ca_type="MSCA"`` only. Returns a
  ``WorkflowRequest`` describing the async replacement job.
* ``GET    /suite-api/api/fleet-management/certificate-management/certificate-authorities``
  — fetch current fleet CA configuration.
* ``PUT    /suite-api/api/fleet-management/certificate-management/certificate-authorities``
  — save / update fleet CA configuration.
* ``GET    /suite-api/api/fleet-management/certificate-management/csrs``
  — list existing Certificate Signing Requests; optional ``commonName`` filter.
* ``POST   /suite-api/api/fleet-management/certificate-management/csrs``
  — generate a new CSR for a certificate; returns a ``WorkflowRequest``.

Auth is the same VCF Operations bearer-token surface used by every other
``vcfops_*`` client (see :mod:`saltext.vcf.utils.vcfops`).

This module complements :mod:`saltext.vcf.clients.vcfops_certificate` (which
manages the *truststore*) and :mod:`saltext.vcf.clients.vcfops_fleet_passwords`
(which manages fleet passwords). Certificate replacement jobs and CSR generation
are asynchronous; poll ``GET /suite-api/api/workflows/requests/{requestId}``
until ``state`` is ``COMPLETED``.
"""

from datetime import datetime
from datetime import timezone

from saltext.vcf.utils import vcfops

_BASE = "/suite-api/api/fleet-management/certificate-management"

DEFAULT_EXPIRY_THRESHOLD_DAYS = 90


def _iso(ms):
    """Convert a unix-ms timestamp to an ISO-8601 ``Z`` string, or ``None``.

    Zero (or absent) means the certificate has no tracked expiry; preserve
    that as ``None`` so callers can distinguish "no expiry info" from
    "expires now".
    """
    if not ms:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _enrich(cert):
    """Return a copy of *cert* with ``expiryDateIso`` added."""
    out = dict(cert)
    out["expiryDateIso"] = _iso(cert.get("expiryDate"))
    return out


# ---------------------------------------------------------------------------
# Query / list
# ---------------------------------------------------------------------------


def query_certificates(
    opts,
    *,
    appliance=None,
    appliance_fqdn=None,
    status=None,
    category=None,
    page=0,
    page_size=20,
    profile=None,
):
    """Raw paginated search; returns the unmodified ``VcfCertificatesResponse``.

    Most callers want :func:`list_` (walks pagination, enriches records with
    ``expiryDateIso``); this is the low-level handle for clients that need
    fine-grained control over paging.

    Filter parameters:

    appliance
        Appliance type string, e.g. ``"VCENTER"``, ``"NSX"``,
        ``"IDENTITY_BROKER"``, ``"SDDC_MANAGER"``.
    appliance_fqdn
        Filter to a specific appliance by its fully-qualified domain name.
    status
        Certificate status: ``"NORMAL"``, ``"EXPIRING"``, ``"EXPIRED"``,
        ``"UNKNOWN"``.
    category
        Certificate category: e.g. ``"TLS_CERT"``.
    """
    body = {}
    if appliance is not None:
        body["appliance"] = appliance
    if appliance_fqdn is not None:
        body["applianceFqdn"] = appliance_fqdn
    if status is not None:
        body["status"] = status
    if category is not None:
        body["category"] = category
    params = {"page": page, "pageSize": page_size}
    return vcfops.api_post(
        opts, f"{_BASE}/certificates/query", body=body, params=params, profile=profile
    )


def list_(opts, *, profile=None, page_size=100, **filters):
    """List every managed certificate visible to VCF Operations.

    Walks pagination and returns ``{"certificates": [...], "totalCount": N}``.
    Each certificate dict is enriched with ``expiryDateIso`` (the ISO-8601
    rendering of ``expiryDate`` in UTC, or ``None`` when ``expiryDate`` is
    zero or absent).

    *filters* accepts the same keyword arguments as :func:`query_certificates`
    (``appliance``, ``appliance_fqdn``, ``status``, ``category``), enabling
    scope-limited queries such as::

        # All certificates for a single vCenter
        list_(opts, appliance="VCENTER", appliance_fqdn="vc01.example.com")

        # Every expiring certificate across the fleet
        list_(opts, status="EXPIRING")
    """
    certificates = []
    total = 0
    page = 0
    while True:
        resp = query_certificates(opts, page=page, page_size=page_size, profile=profile, **filters)
        chunk = resp.get("vcfCertificateModels", []) or []
        certificates.extend(_enrich(c) for c in chunk)
        page_info = resp.get("pageInfo", {}) or {}
        total = page_info.get("totalCount", len(certificates))
        if not chunk or len(certificates) >= total:
            break
        page += 1
    return {"certificates": certificates, "totalCount": total}


def get(opts, certificate_resource_key, profile=None):
    """Return the certificate record for *certificate_resource_key*, or ``None``.

    Uses the ``GET /certificates/{certificateId}`` endpoint directly rather
    than walking the full list. Returns ``None`` if the API returns an empty
    body (certificate not found).

    The returned dict is enriched with ``expiryDateIso`` like records from
    :func:`list_`.
    """
    resp = vcfops.api_get(
        opts,
        f"{_BASE}/certificates/{certificate_resource_key}",
        profile=profile,
    )
    if resp:
        return _enrich(resp)
    return None


# ---------------------------------------------------------------------------
# Expiry check
# ---------------------------------------------------------------------------


def check_expiry(opts, *, threshold_days=DEFAULT_EXPIRY_THRESHOLD_DAYS, profile=None, **filters):
    """Categorize certificates into ``ok`` / ``expiring`` / ``noExpiry`` buckets.

    *threshold_days* — certificates whose ``expiryDate`` is within this many
    days of "now" land in ``expiring`` (including already-expired certificates,
    which have a negative ``daysUntilExpiry``). Default 90.

    Returns::

        {
            "ok": [...],            # daysUntilExpiry > threshold_days
            "expiring": [...],      # daysUntilExpiry <= threshold_days (incl. expired)
            "noExpiry": [...],      # expiryDate == 0 or absent
            "okCount": int,
            "expiringCount": int,
            "noExpiryCount": int,
            "totalCount": int,
            "expiryThresholdDays": threshold_days,
        }

    Each ``ok`` / ``expiring`` certificate is augmented with
    ``daysUntilExpiry`` (float, rounded to 1 decimal place). ``noExpiry``
    entries are returned as-is.

    *filters* accepts the same keyword arguments as :func:`list_`, so callers
    can scope the check to a specific appliance type, FQDN, or category::

        # Check all NSX certificates
        check_expiry(opts, appliance="NSX")

        # Check the machine SSL cert of one vCenter only
        check_expiry(opts, appliance="VCENTER", appliance_fqdn="vc01.example.com")
    """
    listing = list_(opts, profile=profile, **filters)
    now_ms = datetime.now(tz=timezone.utc).timestamp() * 1000
    threshold_ms = threshold_days * 86400 * 1000

    ok = []
    expiring = []
    no_expiry = []
    for cert in listing["certificates"]:
        exp = cert.get("expiryDate") or 0
        if exp == 0:
            no_expiry.append(cert)
            continue
        delta = exp - now_ms
        bucketed = dict(cert, daysUntilExpiry=round(delta / 86400000, 1))
        if delta <= threshold_ms:
            expiring.append(bucketed)
        else:
            ok.append(bucketed)

    return {
        "ok": ok,
        "expiring": expiring,
        "noExpiry": no_expiry,
        "okCount": len(ok),
        "expiringCount": len(expiring),
        "noExpiryCount": len(no_expiry),
        "totalCount": listing["totalCount"],
        "expiryThresholdDays": threshold_days,
    }


# ---------------------------------------------------------------------------
# Certificate replacement
# ---------------------------------------------------------------------------


def replace(
    opts,
    certificate_resource_key,
    ca_type,
    *,
    certificate_chain=None,
    profile=None,
):
    """Replace the certificate identified by *certificate_resource_key*.

    *ca_type* must be one of:

    ``"EXTERNAL_CA"``
        Supply the signed certificate chain in *certificate_chain* — a PEM
        string containing the leaf certificate followed by the CA chain,
        with ``\\n`` as the line separator.
    ``"MSCA"``
        Integrated Microsoft CA workflow. VCF Operations contacts the
        configured MSCA, signs the pending CSR, and installs the certificate
        automatically; *certificate_chain* is not required.

    Returns the ``WorkflowRequest`` dict (``requestId``, ``requestName``,
    ``state``, ``errorCause``, ``duration``, ``category``, …). Certificate
    replacement is asynchronous and may take several minutes; poll
    ``GET /suite-api/api/workflows/requests/{requestId}`` until ``state``
    is ``COMPLETED`` or ``FAILED``.
    """
    body = {"caType": ca_type}
    if certificate_chain is not None:
        body["certificateChain"] = certificate_chain
    return vcfops.api_put(
        opts,
        f"{_BASE}/certificates/{certificate_resource_key}",
        body=body,
        profile=profile,
    )


# ---------------------------------------------------------------------------
# CSR operations
# ---------------------------------------------------------------------------


def list_csrs(opts, *, common_name=None, profile=None):
    """Return the list of existing Certificate Signing Requests.

    *common_name* filters results to CSRs whose ``commonName`` matches the
    given FQDN. Returns the raw ``certificateSignatureInfo`` list from the
    API response (each entry contains ``id``, ``applianceHostname``,
    ``commonName``, and ``csr`` PEM text).
    """
    params = {}
    if common_name is not None:
        params["commonName"] = common_name
    resp = vcfops.api_get(opts, f"{_BASE}/csrs", params=params or None, profile=profile)
    return resp.get("certificateSignatureInfo", []) or []


def generate_csr(
    opts,
    certificate_resource_key,
    *,
    common_name,
    organization,
    org_unit,
    locality,
    state,
    country,
    subject_alt_names=None,
    email=None,
    key_size="KEY_2048",
    key_algorithm="RSA",
    profile=None,
):
    """Generate a Certificate Signing Request for *certificate_resource_key*.

    The CSR is generated asynchronously. The returned ``WorkflowRequest`` dict
    (``requestId``, ``state``, …) should be polled via
    ``GET /suite-api/api/workflows/requests/{requestId}`` until ``state`` is
    ``COMPLETED``, after which the PEM-encoded CSR is retrievable via
    :func:`list_csrs` filtered by *common_name*.

    Parameters
    ----------
    certificate_resource_key:
        The ``certificateResourceKey`` UUID returned by :func:`list_` or
        :func:`get`.
    common_name:
        The CN (typically the appliance FQDN) for the new certificate.
    subject_alt_names:
        Dict matching the API ``subjectAltNames`` schema, e.g.
        ``{"dns": ["vc01.example.com"], "ip": ["10.0.0.1"]}``.
    key_size:
        RSA key size; accepted values: ``"KEY_2048"``, ``"KEY_3072"``,
        ``"KEY_4096"``. Default ``"KEY_2048"``.
    key_algorithm:
        Key algorithm; accepted values: ``"RSA"``. Default ``"RSA"``.
    """
    spec = {
        "commonName": common_name,
        "organization": organization,
        "orgUnit": org_unit,
        "locality": locality,
        "state": state,
        "country": country,
        "keySize": key_size,
        "keyAlgorithm": key_algorithm,
    }
    if email is not None:
        spec["email"] = email
    if subject_alt_names is not None:
        spec["subjectAltNames"] = subject_alt_names
    body = {"certificateId": certificate_resource_key, "generateCsrSpec": spec}
    return vcfops.api_post(opts, f"{_BASE}/csrs", body=body, profile=profile)


# ---------------------------------------------------------------------------
# CA configuration
# ---------------------------------------------------------------------------


def get_certificate_authorities(opts, profile=None):
    """Return the current fleet Certificate Authority configuration.

    The response schema varies by CA type (MSCA, custom CA, etc.); it is
    returned as-is from the API.
    """
    return vcfops.api_get(opts, f"{_BASE}/certificate-authorities", profile=profile)


def configure_certificate_authorities(opts, config, profile=None):
    """Update the fleet CA configuration.

    *config* is a dict matching the ``VcfCertificateAuthorityConfig`` schema,
    for example::

        # Microsoft CA integration
        {
            "caType": "MSCA",
            "serverUrl": "https://dc1.example.com/certsrv",
            "username": "svc-vcf",
            "password": "...",
            "templateName": "VCFMachineSSL",
        }

    Returns the updated CA configuration as returned by the API.
    """
    return vcfops.api_put(opts, f"{_BASE}/certificate-authorities", body=config, profile=profile)
