"""NSX Management API — cluster status (singleton) and API VIP.

The management-plane cluster VIP is exposed only via the Manager API
(``/api/v1/cluster/api-virtual-ip``); there is no equivalent surface on the
Policy API. Reference: NSX-T API guide, "Cluster Management" section on
developer.broadcom.com.
"""

from saltext.vcf.utils import nsx


def status(opts, profile=None):
    """Return cluster status: cluster_id, mgmt/control statuses, overall_status."""
    return nsx.api_get(opts, "/api/v1/cluster/status", profile=profile)


def api_virtual_ip_get(opts, profile=None):
    """Return the current management-plane cluster VIP.

    Response shape: ``{"ip_address": "1.2.3.4"}`` (``ip_address`` may be
    the empty string when no VIP is set).
    """
    return nsx.api_get(opts, "/api/v1/cluster/api-virtual-ip", profile=profile)


def api_virtual_ip_set(opts, ip_address, profile=None):
    """Set the management-plane cluster VIP to *ip_address*.

    Emits ``POST /api/v1/cluster/api-virtual-ip?action=set_virtual_ip&ip_address=...``.
    NSX validates that the IP is reachable on the manager management network
    before accepting the request.
    """
    return nsx.api_post(
        opts,
        "/api/v1/cluster/api-virtual-ip",
        params={"action": "set_virtual_ip", "ip_address": ip_address},
        profile=profile,
    )


def api_virtual_ip_clear(opts, profile=None):
    """Clear the management-plane cluster VIP.

    Emits ``POST /api/v1/cluster/api-virtual-ip?action=clear_virtual_ip``.
    After clearing, NSX returns ``ip_address`` as an empty string on GET.
    """
    return nsx.api_post(
        opts,
        "/api/v1/cluster/api-virtual-ip",
        params={"action": "clear_virtual_ip"},
        profile=profile,
    )
