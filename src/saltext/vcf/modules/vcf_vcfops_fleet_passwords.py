"""Execution module for VCF Operations fleet password management."""

from saltext.vcf.clients import vcfops_fleet_passwords as c

__virtualname__ = "vcf_vcfops_fleet_passwords"


def __virtual__():
    return __virtualname__


def query_accounts(
    appliance=None,
    appliance_fqdn=None,
    status=None,
    username=None,
    vcf_domain_id=None,
    page=0,
    page_size=10,
    sort_by=None,
    sort_order=None,
    profile=None,
):
    """Raw paginated password-account search.

    Returns the unmodified ``VcfPasswordAccountsResponse``. Most callers
    want :func:`list_`.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_fleet_passwords.query_accounts status=EXPIRING
    """
    return c.query_accounts(
        __opts__,
        appliance=appliance,
        appliance_fqdn=appliance_fqdn,
        status=status,
        username=username,
        vcf_domain_id=vcf_domain_id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        profile=profile,
    )


def list_(
    appliance=None,
    appliance_fqdn=None,
    status=None,
    username=None,
    vcf_domain_id=None,
    profile=None,
):
    """List every managed password account.

    Returns ``{"accounts": [...], "totalCount": N}``. Each account is
    enriched with an ``expiryDateIso`` field.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_fleet_passwords.list_
        salt '*' vcf_vcfops_fleet_passwords.list_ appliance=NSXT_EDGE
    """
    return c.list_(
        __opts__,
        appliance=appliance,
        appliance_fqdn=appliance_fqdn,
        status=status,
        username=username,
        vcf_domain_id=vcf_domain_id,
        profile=profile,
    )


def get_account(password_account_key, profile=None):
    """Return one password account by ``passwordAccountKey``, or ``None``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_fleet_passwords.get_account <password_account_key>
    """
    return c.get_account(__opts__, password_account_key, profile=profile)


def check_expiry(
    threshold_days=c.DEFAULT_EXPIRY_THRESHOLD_DAYS,
    appliance=None,
    appliance_fqdn=None,
    vcf_domain_id=None,
    profile=None,
):
    """Categorize accounts into ``ok`` / ``expiring`` / ``noExpiry`` buckets.

    *threshold_days* — accounts within this many days of expiry land in
    ``expiring`` (including already-expired accounts). Default 90.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_fleet_passwords.check_expiry
        salt '*' vcf_vcfops_fleet_passwords.check_expiry threshold_days=30
    """
    return c.check_expiry(
        __opts__,
        threshold_days=threshold_days,
        appliance=appliance,
        appliance_fqdn=appliance_fqdn,
        vcf_domain_id=vcf_domain_id,
        profile=profile,
    )


def update(password_account_key, current_password, new_password, username=None, profile=None):
    """Rotate a managed password.

    Returns the ``WorkflowRequest`` for the async rotation job.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfops_fleet_passwords.update <password_account_key> <current_password> <new_password>
    """
    return c.update(
        __opts__,
        password_account_key,
        current_password,
        new_password,
        username=username,
        profile=profile,
    )
