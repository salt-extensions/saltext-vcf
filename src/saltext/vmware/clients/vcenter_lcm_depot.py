"""vCenter Lifecycle Manager (LCM) software depots.

Depots are the sources vCenter uses to compose cluster images (vSphere
Lifecycle Manager). Terraform's ``vsphere_offline_software_depot`` manages
*offline* (zip-bundle) depots; this client covers both offline and online
forms uniformly under ``/api/esx/settings/depots``.

Operations:

- List / get / create / delete a depot config (where the depot lives).
- Trigger / poll a depot sync.
- List the bundle content currently downloaded from a depot.
"""

import requests

from saltext.vmware.utils import vcenter

DEPOTS = "/api/esx/settings/depots"
OFFLINE = f"{DEPOTS}/offline"
ONLINE = f"{DEPOTS}/online"
UMDS = f"{DEPOTS}/umds"


def _per_id(path):
    def _list(opts, profile=None):
        return vcenter.api_get(opts, path, profile=profile)

    def _get(opts, depot_id, profile=None):
        return vcenter.api_get(opts, f"{path}/{depot_id}", profile=profile)

    def _get_or_none(opts, depot_id, profile=None):
        try:
            return _get(opts, depot_id, profile=profile)
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                return None
            raise

    def _delete(opts, depot_id, profile=None):
        return vcenter.api_delete(opts, f"{path}/{depot_id}", profile=profile)

    return _list, _get, _get_or_none, _delete


# Offline depots
list_offline, get_offline, get_offline_or_none, delete_offline = _per_id(OFFLINE)


def create_offline(opts, file_locator, profile=None, **spec):
    """Create an offline depot from an uploaded zip.

    *file_locator* points at a content-library item or a vCenter-hosted file
    path (``/storage/updatemgr/...``).
    """
    body = {"file_locator": file_locator}
    body.update(spec)
    return vcenter.api_post(opts, OFFLINE, body=body, profile=profile)


# Online depots
list_online, get_online, get_online_or_none, delete_online = _per_id(ONLINE)


def create_online(opts, location, profile=None, **spec):
    """Create an online depot pointing at a URL."""
    body = {"location": location}
    body.update(spec)
    return vcenter.api_post(opts, ONLINE, body=body, profile=profile)


# UMDS (Update Manager Download Service) depots
list_umds, get_umds, get_umds_or_none, delete_umds = _per_id(UMDS)


def create_umds(opts, location, profile=None, **spec):
    body = {"location": location}
    body.update(spec)
    return vcenter.api_post(opts, UMDS, body=body, profile=profile)


# Sync / content


def sync(opts, profile=None):
    """Trigger a sync across all online/UMDS depots. Returns a task identifier."""
    return vcenter.api_post(opts, DEPOTS, params={"action": "sync"}, profile=profile)


def get_content(opts, profile=None):
    """Return the union of bundles + components currently in the depot."""
    return vcenter.api_get(opts, f"{DEPOTS}/content", profile=profile)
