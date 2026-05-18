"""Execution module for VCF Fleet Management password administration."""

from saltext.vcf.clients import fleet_password as c

__virtualname__ = "vcf_fleet_password"


def __virtual__():
    return __virtualname__


def list_accounts(profile=None):
    """List every managed credential in the fleet.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_fleet_password.list_accounts
    """
    return c.list_accounts(__opts__, profile=profile)


def get_account(account_key, profile=None):
    """Return one account record.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_fleet_password.get_account <account_key>
    """
    return c.get_account(__opts__, account_key, profile=profile)


def get_password(account_key, profile=None):
    """Retrieve the current password (treat the return value as a secret).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_fleet_password.get_password <account_key>
    """
    return c.get_password(__opts__, account_key, profile=profile)


def set_password(account_key, new_password, profile=None):
    """Rotate to an operator-supplied password.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_fleet_password.set_password <account_key> <new_password>
    """
    return c.set_password(__opts__, account_key, new_password, profile=profile)


def rotate(account_key, profile=None):
    """Trigger an auto-generated rotation.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_fleet_password.rotate <account_key>
    """
    return c.rotate(__opts__, account_key, profile=profile)


def history(account_key, profile=None):
    """Return rotation history.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_fleet_password.history <account_key>
    """
    return c.history(__opts__, account_key, profile=profile)
