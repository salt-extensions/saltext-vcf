"""vCenter Content Library — libraries + items + OVF deploy."""

import requests

from saltext.vcf.utils import vcenter

LIBRARY = "/api/content/library"
LOCAL_LIBRARY = "/api/content/local-library"
SUBSCRIBED_LIBRARY = "/api/content/subscribed-library"
ITEM = "/api/content/library/item"
UPDATE_SESSION = "/api/content/library/item/update-session"
UPDATE_SESSION_FILE = "/api/content/library/item/updatesession/file"
OVF_ITEM = "/api/vcenter/ovf/library-item"
VM_TEMPLATE = "/api/vcenter/vm-template/library-items"


def list_(opts, profile=None):
    """List all content library IDs."""
    return vcenter.api_get(opts, LIBRARY, profile=profile)


def get(opts, library_id, profile=None):
    return vcenter.api_get(opts, f"{LIBRARY}/{library_id}", profile=profile)


def get_or_none(opts, library_id, profile=None):
    try:
        return get(opts, library_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def list_local(opts, profile=None):
    return vcenter.api_get(opts, LOCAL_LIBRARY, profile=profile)


def create_local(opts, name, storage_backings, profile=None, **spec):
    """Create a local content library.

    *storage_backings* is a list like
    ``[{"type": "DATASTORE", "datastore_id": "datastore-12"}]``.
    """
    body = {
        "name": name,
        "type": "LOCAL",
        "storage_backings": list(storage_backings),
        "publish_info": spec.pop("publish_info", None),
    }
    body.update(spec)
    return vcenter.api_post(opts, LOCAL_LIBRARY, body={"create_spec": body, "client_token": ""})


def delete_local(opts, library_id, profile=None):
    return vcenter.api_delete(opts, f"{LOCAL_LIBRARY}/{library_id}", profile=profile)


def list_subscribed(opts, profile=None):
    return vcenter.api_get(opts, SUBSCRIBED_LIBRARY, profile=profile)


def create_subscribed(opts, name, subscription_url, storage_backings, profile=None, **spec):
    """Create a subscribed content library."""
    body = {
        "name": name,
        "type": "SUBSCRIBED",
        "subscription_info": {
            "subscription_url": subscription_url,
            **spec.pop("subscription_info", {}),
        },
        "storage_backings": list(storage_backings),
    }
    body.update(spec)
    return vcenter.api_post(
        opts, SUBSCRIBED_LIBRARY, body={"create_spec": body, "client_token": ""}
    )


def delete_subscribed(opts, library_id, profile=None):
    return vcenter.api_delete(opts, f"{SUBSCRIBED_LIBRARY}/{library_id}", profile=profile)


def list_items(opts, library_id, profile=None):
    """List item IDs in a content library."""
    return vcenter.api_get(opts, ITEM, params={"library_id": library_id}, profile=profile)


def get_item(opts, item_id, profile=None):
    return vcenter.api_get(opts, f"{ITEM}/{item_id}", profile=profile)


def get_item_or_none(opts, item_id, profile=None):
    try:
        return get_item(opts, item_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def delete_item(opts, item_id, profile=None):
    return vcenter.api_delete(opts, f"{ITEM}/{item_id}", profile=profile)


# -- library write paths --------------------------------------------------


def update_local(opts, library_id, spec, profile=None):
    """PATCH a local content library (rename, change publish_info, etc.)."""
    return vcenter.api_patch(
        opts, f"{LOCAL_LIBRARY}/{library_id}", body={"update_spec": dict(spec)}, profile=profile
    )


def update_subscribed(opts, library_id, spec, profile=None):
    """PATCH a subscribed content library (change url, password, auto sync...)."""
    return vcenter.api_patch(
        opts,
        f"{SUBSCRIBED_LIBRARY}/{library_id}",
        body={"update_spec": dict(spec)},
        profile=profile,
    )


def sync_subscribed(opts, library_id, profile=None):
    """Trigger an immediate sync of a subscribed library."""
    return vcenter.api_post(
        opts, f"{SUBSCRIBED_LIBRARY}/{library_id}", params={"action": "sync"}, profile=profile
    )


def publish_library(opts, library_id, subscriptions=None, profile=None):
    """Publish a local library to its subscribers.

    *subscriptions* is an optional list of subscription IDs; if None, publish to all.
    """
    body = {}
    if subscriptions is not None:
        body["subscriptions"] = [{"id": s} for s in subscriptions]
    return vcenter.api_post(
        opts,
        f"{LOCAL_LIBRARY}/{library_id}",
        body=body or None,
        params={"action": "publish"},
        profile=profile,
    )


def find_libraries(opts, name=None, type=None, profile=None):  # pylint: disable=redefined-builtin
    """Search for libraries by name/type."""
    spec = {}
    if name is not None:
        spec["name"] = name
    if type is not None:
        spec["type"] = type
    return vcenter.api_post(opts, LIBRARY, body=spec, params={"action": "find"}, profile=profile)


# -- item write paths -----------------------------------------------------


def create_item(
    opts, library_id, name, type, profile=None, **spec
):  # pylint: disable=redefined-builtin
    """Create an empty library item; populate via an update session."""
    body = {"library_id": library_id, "name": name, "type": type}
    body.update(spec)
    return vcenter.api_post(
        opts, ITEM, body={"create_spec": body, "client_token": ""}, profile=profile
    )


def update_item(opts, item_id, spec, profile=None):
    """PATCH a library item (rename, change description, change type)."""
    return vcenter.api_patch(
        opts, f"{ITEM}/{item_id}", body={"update_spec": dict(spec)}, profile=profile
    )


def find_items(
    opts, library_id=None, name=None, type=None, profile=None
):  # pylint: disable=redefined-builtin
    spec = {}
    if library_id is not None:
        spec["library_id"] = library_id
    if name is not None:
        spec["name"] = name
    if type is not None:
        spec["type"] = type
    return vcenter.api_post(opts, ITEM, body=spec, params={"action": "find"}, profile=profile)


# -- update sessions ------------------------------------------------------


def update_session_create(opts, item_id, profile=None, **spec):
    """Open an update session against *item_id*. Returns the session id."""
    body = {"library_item_id": item_id}
    body.update(spec)
    return vcenter.api_post(
        opts, UPDATE_SESSION, body={"create_spec": body, "client_token": ""}, profile=profile
    )


def update_session_get(opts, session_id, profile=None):
    return vcenter.api_get(opts, f"{UPDATE_SESSION}/{session_id}", profile=profile)


def update_session_complete(opts, session_id, profile=None):
    return vcenter.api_post(
        opts, f"{UPDATE_SESSION}/{session_id}", params={"action": "complete"}, profile=profile
    )


def update_session_cancel(opts, session_id, profile=None):
    return vcenter.api_post(
        opts, f"{UPDATE_SESSION}/{session_id}", params={"action": "cancel"}, profile=profile
    )


def update_session_fail(opts, session_id, error, profile=None):
    return vcenter.api_post(
        opts,
        f"{UPDATE_SESSION}/{session_id}",
        body={"client_error_message": error},
        params={"action": "fail"},
        profile=profile,
    )


def update_session_keep_alive(opts, session_id, profile=None):
    return vcenter.api_post(
        opts, f"{UPDATE_SESSION}/{session_id}", params={"action": "keep-alive"}, profile=profile
    )


def update_session_add_file(opts, session_id, name, source_type="PUSH", profile=None, **spec):
    """Register a file for upload into an update session.

    Returns a structure with an ``upload_endpoint`` URI the caller PUTs bytes to
    (when *source_type* is ``PUSH``).
    """
    body = {"name": name, "source_type": source_type}
    body.update(spec)
    return vcenter.api_post(
        opts,
        UPDATE_SESSION_FILE,
        body={"update_session_id": session_id, "file_spec": body},
        params={"action": "add"},
        profile=profile,
    )


def update_session_list_files(opts, session_id, profile=None):
    return vcenter.api_post(
        opts,
        UPDATE_SESSION_FILE,
        body={"update_session_id": session_id},
        params={"action": "list"},
        profile=profile,
    )


# -- OVF deploy / create_from_vm ------------------------------------------


def ovf_deploy(opts, library_item_id, deployment_target, deployment_spec, profile=None):
    """Deploy an OVF library item to a target resource pool/folder/host.

    *deployment_target* — ``{"resource_pool_id": ..., "folder_id": ..., "host_id": ...}``
    *deployment_spec*   — ``{"name": ..., "accept_all_eula": true, ...}``
    """
    body = {
        "target": deployment_target,
        "deployment_spec": deployment_spec,
    }
    return vcenter.api_post(
        opts,
        f"{OVF_ITEM}/{library_item_id}",
        body=body,
        params={"action": "deploy"},
        profile=profile,
    )


def ovf_filter(opts, library_item_id, deployment_target, profile=None):
    """Return the OVF item's network/storage/disk inventory bound to a target."""
    return vcenter.api_post(
        opts,
        f"{OVF_ITEM}/{library_item_id}",
        body={"target": deployment_target},
        params={"action": "filter"},
        profile=profile,
    )


def ovf_create_from_vm(opts, vm_id, create_spec, profile=None):
    """Export *vm_id* as a new OVF library item."""
    body = {"source": {"type": "VirtualMachine", "id": vm_id}, "create_spec": create_spec}
    return vcenter.api_post(
        opts, OVF_ITEM, body=body, params={"action": "create_from_vm_template"}, profile=profile
    )


# -- VM template library items (vSphere 6.7+) -----------------------------


def vm_template_get(opts, item_id, profile=None):
    return vcenter.api_get(opts, f"{VM_TEMPLATE}/{item_id}", profile=profile)


def vm_template_get_or_none(opts, item_id, profile=None):
    try:
        return vm_template_get(opts, item_id, profile=profile)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def vm_template_create(opts, create_spec, profile=None):
    """Capture a VM as a VM-template library item.

    *create_spec* must include ``name``, ``library``, ``source_vm`` and a
    ``placement`` block.
    """
    return vcenter.api_post(opts, VM_TEMPLATE, body={"spec": create_spec}, profile=profile)


def vm_template_deploy(opts, item_id, deploy_spec, profile=None):
    """Deploy a new VM from a VM-template library item."""
    return vcenter.api_post(
        opts,
        f"{VM_TEMPLATE}/{item_id}",
        body={"spec": deploy_spec},
        params={"action": "deploy"},
        profile=profile,
    )
