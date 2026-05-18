"""VCF Installer system endpoints — status, version, registration, DNS/NTP."""

import requests

from saltext.vcf.utils import installer


def status(opts, profile=None):
    """Return installer health + readiness state."""
    return installer.api_get(opts, "/v1/system/status", profile=profile)


def version(opts, profile=None):
    """Return installer build/version metadata."""
    return installer.api_get(opts, "/v1/system/version", profile=profile)


def registration(opts, profile=None):
    """Return Customer Connect / VCF registration state."""
    return installer.api_get(opts, "/v1/system/registration", profile=profile)


def registration_or_none(opts, profile=None):
    try:
        return registration(opts, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def dns_config(opts, profile=None):
    """Return the installer appliance's own DNS configuration."""
    return installer.api_get(opts, "/v1/system/dns-config", profile=profile)


def update_dns_config(opts, dns_servers, search_domains=None, profile=None):
    body = {"dnsServers": list(dns_servers)}
    if search_domains is not None:
        body["dnsSearchDomains"] = list(search_domains)
    return installer.api_patch(opts, "/v1/system/dns-config", body=body, profile=profile)


def ntp_config(opts, profile=None):
    """Return the installer appliance's own NTP configuration."""
    return installer.api_get(opts, "/v1/system/ntp-config", profile=profile)


def update_ntp_config(opts, ntp_servers, profile=None):
    return installer.api_patch(
        opts, "/v1/system/ntp-config", body={"ntpServers": list(ntp_servers)}, profile=profile
    )


def identity_broker(opts, profile=None):
    """Return Identity Broker configuration the installer will hand off."""
    return installer.api_get(opts, "/v1/identity-broker-information", profile=profile)


def sddc_manager(opts, profile=None):
    """Return the SDDC Manager info that bringup deployed (post-bringup only)."""
    return installer.api_get(opts, "/v1/sddc-manager-system/sddc-manager", profile=profile)


def sddc_manager_or_none(opts, profile=None):
    try:
        return sddc_manager(opts, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise
