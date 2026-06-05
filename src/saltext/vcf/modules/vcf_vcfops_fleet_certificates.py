"""Execution module for VCF Operations fleet certificate management."""

from saltext.vcf.clients import vcfops_fleet_certificates as c

__virtualname__ = "vcf_vcfops_fleet_certificates"


def __virtual__():
    return __virtualname__


def query_certificates(
    appliance=None,
    appliance_fqdn=None,
    status=None,
    category=None,
    page=0,
    page_size=1000,
    profile=None,
):
    """Raw paginated certificate search.

    Returns the unmodified ``VcfCertificatesResponse``. Most callers want
    :func:`list_`.

    appliance
        Appliance type, e.g. ``VCENTER``, ``NSX``, ``IDENTITY_BROKER``,
        ``SDDC_MANAGER``.
    appliance_fqdn
        Narrow to a specific appliance FQDN.
    status
        ``NORMAL``, ``EXPIRING``, ``EXPIRED``, or ``UNKNOWN``.
    category
        Certificate category, e.g. ``TLS_CERT``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_fleet_certificates.query_certificates status=EXPIRING
        salt '*' vcf_vcfops_fleet_certificates.query_certificates appliance=VCENTER category=TLS_CERT
    """
    return c.query_certificates(
        __opts__,
        appliance=appliance,
        appliance_fqdn=appliance_fqdn,
        status=status,
        category=category,
        page=page,
        page_size=page_size,
        profile=profile,
    )


def list_(
    appliance=None,
    appliance_fqdn=None,
    status=None,
    category=None,
    profile=None,
):
    """List managed certificates across the fleet.

    Walks pagination and returns ``{"certificates": [...], "totalCount": N}``.
    Each certificate is enriched with an ``expiryDateIso`` field (ISO-8601 UTC).

    appliance
        Filter by appliance type, e.g. ``VCENTER``, ``NSX``,
        ``IDENTITY_BROKER``, ``SDDC_MANAGER``.
    appliance_fqdn
        Filter to a specific appliance by FQDN.
    status
        ``NORMAL``, ``EXPIRING``, ``EXPIRED``, or ``UNKNOWN``.
    category
        Certificate category, e.g. ``TLS_CERT``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_fleet_certificates.list_
        salt '*' vcf_vcfops_fleet_certificates.list_ appliance=VCENTER
        salt '*' vcf_vcfops_fleet_certificates.list_ status=EXPIRING category=TLS_CERT
        salt '*' vcf_vcfops_fleet_certificates.list_ appliance=NSX appliance_fqdn=nsx01.example.com
    """
    return c.list_(
        __opts__,
        appliance=appliance,
        appliance_fqdn=appliance_fqdn,
        status=status,
        category=category,
        profile=profile,
    )


def get(certificate_resource_key, profile=None):
    """Return one certificate by its ``certificateResourceKey``, or ``None``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_fleet_certificates.get <certificateResourceKey>
    """
    return c.get(__opts__, certificate_resource_key, profile=profile)


def check_expiry(
    threshold_days=c.DEFAULT_EXPIRY_THRESHOLD_DAYS,
    appliance=None,
    appliance_fqdn=None,
    status=None,
    category=None,
    profile=None,
):
    """Categorize certificates into ``ok`` / ``expiring`` / ``noExpiry`` buckets.

    *threshold_days* — certificates within this many days of expiry land in
    ``expiring`` (including already-expired certificates). Default 90.

    Each ``ok`` / ``expiring`` certificate is augmented with a
    ``daysUntilExpiry`` field (float, negative when already expired).

    Returns::

        {
            "ok": [...],
            "expiring": [...],
            "noExpiry": [...],
            "okCount": int,
            "expiringCount": int,
            "noExpiryCount": int,
            "totalCount": int,
            "expiryThresholdDays": int,
        }

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_fleet_certificates.check_expiry
        salt '*' vcf_vcfops_fleet_certificates.check_expiry threshold_days=30
        salt '*' vcf_vcfops_fleet_certificates.check_expiry appliance=VCENTER
        salt '*' vcf_vcfops_fleet_certificates.check_expiry appliance=NSX appliance_fqdn=nsx01.example.com threshold_days=60
    """
    return c.check_expiry(
        __opts__,
        threshold_days=threshold_days,
        appliance=appliance,
        appliance_fqdn=appliance_fqdn,
        status=status,
        category=category,
        profile=profile,
    )


def replace(certificate_resource_key, ca_type, certificate_chain=None, profile=None):
    """Replace the certificate identified by *certificate_resource_key*.

    *ca_type* controls how the replacement is signed:

    ``EXTERNAL_CA``
        Supply the signed PEM chain in *certificate_chain* (leaf cert +
        CA chain concatenated, ``\\n``-separated).
    ``MSCA``
        Integrated Microsoft CA — VCF Operations signs and installs
        automatically; *certificate_chain* is not required.

    Returns the ``WorkflowRequest`` for the async replacement job
    (``requestId``, ``state``, …). Poll the request ID via
    :mod:`vcf_vcfops_task` to track completion.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_fleet_certificates.replace <certificateResourceKey> MSCA
        salt '*' vcf_vcfops_fleet_certificates.replace <certificateResourceKey> EXTERNAL_CA certificate_chain='-----BEGIN CERTIFICATE-----\\n...'
    """
    return c.replace(
        __opts__,
        certificate_resource_key,
        ca_type,
        certificate_chain=certificate_chain,
        profile=profile,
    )


def list_csrs(common_name=None, profile=None):
    """List existing Certificate Signing Requests.

    *common_name* narrows results to CSRs for a specific FQDN.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_fleet_certificates.list_csrs
        salt '*' vcf_vcfops_fleet_certificates.list_csrs common_name=vc01.example.com
    """
    return c.list_csrs(__opts__, common_name=common_name, profile=profile)


def generate_csr(
    certificate_resource_key,
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

    The operation is asynchronous; the returned ``WorkflowRequest``
    (``requestId``, ``state``, …) should be polled until ``state`` is
    ``COMPLETED``, after which the PEM CSR is retrievable via
    :func:`list_csrs` filtered by *common_name*.

    certificate_resource_key
        The ``certificateResourceKey`` UUID from :func:`list_` or
        :func:`get`.
    common_name
        CN for the new certificate (typically the appliance FQDN).
    subject_alt_names
        Dict of SANs, e.g.
        ``'{"dns": ["vc01.example.com"], "ip": ["10.0.0.1"]}'``.
    key_size
        ``KEY_2048`` (default), ``KEY_3072``, or ``KEY_4096``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_fleet_certificates.generate_csr \\
            <certificateResourceKey> \\
            vc01.example.com "Acme Corp" IT Amsterdam NH NL
    """
    return c.generate_csr(
        __opts__,
        certificate_resource_key,
        common_name=common_name,
        organization=organization,
        org_unit=org_unit,
        locality=locality,
        state=state,
        country=country,
        subject_alt_names=subject_alt_names,
        email=email,
        key_size=key_size,
        key_algorithm=key_algorithm,
        profile=profile,
    )


def renew_expiring(
    ca_type,
    threshold_days=c.DEFAULT_EXPIRY_THRESHOLD_DAYS,
    appliance=None,
    appliance_fqdn=None,
    category=None,
    poll_interval=15,
    poll_timeout=600,
    profile=None,
):
    """Find expiring / expired certificates and replace them.

    Discovers certificates expiring within *threshold_days* (default 90) and
    calls the VCF Operations certificate replace API for each one. VCF handles
    key generation and signing internally — no CSR preparation needed.

    ca_type
        ``OPENSSL`` — VCF Operations built-in self-signed CA (no external
        dependency; configure once under Fleet Management → Certificates →
        Configure CA for Fleet → OpenSSL).

        ``MSCA`` — integrated Microsoft CA.

    Returns a report dict::

        {
            "renewed":      [...],
            "failed":       [...],
            "renewedCount": int,
            "failedCount":  int,
            "checkedCount": int,
        }

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_fleet_certificates.renew_expiring OPENSSL
        salt '*' vcf_vcfops_fleet_certificates.renew_expiring OPENSSL threshold_days=30
        salt '*' vcf_vcfops_fleet_certificates.renew_expiring OPENSSL appliance=VCENTER
        salt '*' vcf_vcfops_fleet_certificates.renew_expiring MSCA appliance=NSXT_MANAGER threshold_days=60
    """
    return c.renew_expiring(
        __opts__,
        ca_type=ca_type,
        threshold_days=threshold_days,
        appliance=appliance,
        appliance_fqdn=appliance_fqdn,
        category=category,
        poll_interval=poll_interval,
        poll_timeout=poll_timeout,
        profile=profile,
    )


def get_certificate_authorities(profile=None):
    """Return the current fleet Certificate Authority configuration.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_fleet_certificates.get_certificate_authorities
    """
    return c.get_certificate_authorities(__opts__, profile=profile)


def configure_certificate_authorities(config, profile=None):
    """Update the fleet CA configuration.

    *config* is a dict matching the ``VcfCertificateAuthorityConfig`` schema,
    for example::

        {
            "caType": "MSCA",
            "serverUrl": "https://dc1.example.com/certsrv",
            "username": "svc-vcf",
            "password": "...",
            "templateName": "VCFMachineSSL",
        }

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_fleet_certificates.configure_certificate_authorities \\
            '{"caType": "MSCA", "serverUrl": "https://dc1.example.com/certsrv", "templateName": "VCFMachineSSL"}'
    """
    return c.configure_certificate_authorities(__opts__, config, profile=profile)
