"""NSX Manager appliance NTP configuration via the Node service API."""

from saltext.vcf.utils import nsx

_NTP_SERVICE = "/api/v1/node/services/ntp"


def _read_service(opts, profile=None):
    current = nsx.api_get(opts, _NTP_SERVICE, profile=profile)
    if not isinstance(current, dict):
        raise ValueError("Unexpected NTP service response")
    properties = current.get("service_properties")
    if not isinstance(properties, dict):
        raise ValueError("NTP response is missing service_properties")
    if not isinstance(properties.get("servers"), list):
        raise ValueError("NTP response is missing the servers list")
    return current


def ntp_get(opts, profile=None):
    """Return the server list in the shape expected by the Salt state."""
    current = _read_service(opts, profile=profile)
    return {"ntp_servers": current["service_properties"]["servers"]}


def ntp_set(opts, servers, profile=None):
    """Update NTP servers while preserving other service properties."""
    if not isinstance(servers, (list, tuple)):
        raise ValueError("servers must be a list of NTP server addresses")
    current = _read_service(opts, profile=profile)
    properties = dict(current["service_properties"])
    properties["servers"] = list(servers)
    body = {
        "service_name": current.get("service_name", "ntp"),
        "service_properties": properties,
    }
    return nsx.api_put(opts, _NTP_SERVICE, body=body, profile=profile)
