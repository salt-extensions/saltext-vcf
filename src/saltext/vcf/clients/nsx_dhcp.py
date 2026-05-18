"""NSX DHCP server and relay configurations (Policy API)."""

import requests

from saltext.vcf.utils import nsx

SERVER = "/policy/api/v1/infra/dhcp-server-configs"
RELAY = "/policy/api/v1/infra/dhcp-relay-configs"


def server_list(opts, profile=None):
    return nsx.api_get(opts, SERVER, profile=profile)


def server_get(opts, server_id, profile=None):
    return nsx.api_get(opts, f"{SERVER}/{server_id}", profile=profile)


def server_get_or_none(opts, server_id, profile=None):
    try:
        return server_get(opts, server_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def server_create(opts, server_id, profile=None, **spec):
    body = {"display_name": spec.pop("display_name", server_id)}
    body.update(spec)
    return nsx.api_put(opts, f"{SERVER}/{server_id}", body=body, profile=profile)


def server_delete(opts, server_id, profile=None):
    return nsx.api_delete(opts, f"{SERVER}/{server_id}", profile=profile)


def relay_list(opts, profile=None):
    return nsx.api_get(opts, RELAY, profile=profile)


def relay_get(opts, relay_id, profile=None):
    return nsx.api_get(opts, f"{RELAY}/{relay_id}", profile=profile)


def relay_get_or_none(opts, relay_id, profile=None):
    try:
        return relay_get(opts, relay_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def relay_create(opts, relay_id, server_addresses, profile=None, **spec):
    body = {
        "display_name": spec.pop("display_name", relay_id),
        "server_addresses": list(server_addresses),
    }
    body.update(spec)
    return nsx.api_put(opts, f"{RELAY}/{relay_id}", body=body, profile=profile)


def relay_delete(opts, relay_id, profile=None):
    return nsx.api_delete(opts, f"{RELAY}/{relay_id}", profile=profile)
