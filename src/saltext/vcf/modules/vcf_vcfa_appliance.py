"""Execution module: VCF Automation appliance hardening (TLS, ports, SSH)."""

from saltext.vcf.clients import vcfa_appliance as c

__virtualname__ = "vcf_vcfa_appliance"


def __virtual__():
    return __virtualname__


# -- TLS -------------------------------------------------------------------


def tls_get(profile=None):
    """Return the current appliance TLS configuration.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_appliance.tls_get
    """
    return c.tls_get(__opts__, profile=profile)


def tls_set(protocols=None, cipher_suites=None, profile=None):
    """PUT a new TLS profile (defaults to ``["TLSv1.2","TLSv1.3"]``).

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vcfa_appliance.tls_set '["TLSv1.2","TLSv1.3"]'
    """
    return c.tls_set(
        __opts__, protocols=protocols, cipher_suites=cipher_suites, profile=profile
    )


# -- Services / ports ------------------------------------------------------


def services_list(profile=None):
    """List all appliance services and their enabled/disabled state."""
    return c.services_list(__opts__, profile=profile)


def service_get(service, profile=None):
    """Return one service record, or ``None`` if not present."""
    return c.service_get(__opts__, service, profile=profile)


def service_disable(service, profile=None):
    """Disable *service*. Idempotent — no request if already disabled."""
    return c.service_disable(__opts__, service, profile=profile)


def service_enable(service, profile=None):
    """Enable *service*. Idempotent — no request if already enabled."""
    return c.service_enable(__opts__, service, profile=profile)


def firewall_list(profile=None):
    """Return the appliance port allow-list."""
    return c.firewall_list(__opts__, profile=profile)


# -- SSH -------------------------------------------------------------------


def ssh_get(profile=None):
    """Return the current SSH daemon configuration."""
    return c.ssh_get(__opts__, profile=profile)


def ssh_set(enabled=None, root_enabled=None, admin_enabled=None, profile=None):
    """Update SSH daemon config (enabled / rootLogin / adminLogin)."""
    return c.ssh_set(
        __opts__,
        enabled=enabled,
        root_enabled=root_enabled,
        admin_enabled=admin_enabled,
        profile=profile,
    )
