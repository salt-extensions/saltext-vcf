"""Tests for the T4 content-library write paths."""

import json

import responses

from saltext.vcf.clients import vcenter_content_library as c

BASE = "https://vc.test"


def test_update_local_wraps_body(opts, vcenter_authed):
    vcenter_authed.add(
        responses.PATCH, f"{BASE}/api/content/local-library/lib-1", json={}, status=200
    )
    c.update_local(opts, "lib-1", {"name": "renamed"})
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body["update_spec"] == {"name": "renamed"}


def test_update_subscribed_wraps_body(opts, vcenter_authed):
    vcenter_authed.add(
        responses.PATCH, f"{BASE}/api/content/subscribed-library/lib-2", json={}, status=200
    )
    c.update_subscribed(opts, "lib-2", {"subscription_info": {"automatic_sync_enabled": True}})
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body["update_spec"]["subscription_info"]["automatic_sync_enabled"] is True


def test_sync_subscribed_uses_action_query(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST, f"{BASE}/api/content/subscribed-library/lib-2", json=None, status=200
    )
    c.sync_subscribed(opts, "lib-2")
    assert "action=sync" in vcenter_authed.calls[-1].request.url


def test_publish_library_no_subscribers(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST, f"{BASE}/api/content/local-library/lib-1", json=None, status=200
    )
    c.publish_library(opts, "lib-1")
    req = vcenter_authed.calls[-1].request
    assert "action=publish" in req.url
    assert req.body in (None, b"", b"null")


def test_publish_library_with_subscribers(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST, f"{BASE}/api/content/local-library/lib-1", json=None, status=200
    )
    c.publish_library(opts, "lib-1", subscriptions=["sub-a", "sub-b"])
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {"subscriptions": [{"id": "sub-a"}, {"id": "sub-b"}]}


def test_find_libraries_posts_spec(opts, vcenter_authed):
    vcenter_authed.add(responses.POST, f"{BASE}/api/content/library", json=["lib-1"], status=200)
    out = c.find_libraries(opts, name="MyLib", type="LOCAL")
    assert out == ["lib-1"]
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {"name": "MyLib", "type": "LOCAL"}
    assert "action=find" in vcenter_authed.calls[-1].request.url


def test_create_item_wraps_create_spec(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST, f"{BASE}/api/content/library/item", json="item-99", status=200
    )
    assert c.create_item(opts, "lib-1", "myitem", "ovf") == "item-99"
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body["create_spec"] == {"library_id": "lib-1", "name": "myitem", "type": "ovf"}
    assert body["client_token"] == ""


def test_update_item_wraps_body(opts, vcenter_authed):
    vcenter_authed.add(
        responses.PATCH, f"{BASE}/api/content/library/item/item-1", json={}, status=200
    )
    c.update_item(opts, "item-1", {"name": "newname"})
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body["update_spec"] == {"name": "newname"}


def test_find_items_posts_spec(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST, f"{BASE}/api/content/library/item", json=["item-1"], status=200
    )
    c.find_items(opts, library_id="lib-1", name="foo")
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {"library_id": "lib-1", "name": "foo"}
    assert "action=find" in vcenter_authed.calls[-1].request.url


# -- update sessions ------------------------------------------------------


def test_update_session_create(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        f"{BASE}/api/content/library/item/update-session",
        json="session-1",
        status=200,
    )
    assert c.update_session_create(opts, "item-1") == "session-1"
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body["create_spec"]["library_item_id"] == "item-1"


def test_update_session_lifecycle_actions(opts, vcenter_authed):
    for _ in ("complete", "cancel", "keep-alive"):
        vcenter_authed.add(
            responses.POST,
            f"{BASE}/api/content/library/item/update-session/session-1",
            json=None,
            status=200,
        )
    c.update_session_complete(opts, "session-1")
    assert "action=complete" in vcenter_authed.calls[-1].request.url
    c.update_session_cancel(opts, "session-1")
    assert "action=cancel" in vcenter_authed.calls[-1].request.url
    c.update_session_keep_alive(opts, "session-1")
    assert "action=keep-alive" in vcenter_authed.calls[-1].request.url


def test_update_session_fail_body(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        f"{BASE}/api/content/library/item/update-session/session-1",
        json=None,
        status=200,
    )
    c.update_session_fail(opts, "session-1", "boom")
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {"client_error_message": "boom"}
    assert "action=fail" in vcenter_authed.calls[-1].request.url


def test_update_session_add_file(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        f"{BASE}/api/content/library/item/updatesession/file",
        json={"upload_endpoint": {"uri": "https://vc.test/upload/x"}},
        status=200,
    )
    out = c.update_session_add_file(opts, "session-1", "disk.vmdk")
    assert out["upload_endpoint"]["uri"].endswith("/upload/x")
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body["update_session_id"] == "session-1"
    assert body["file_spec"]["name"] == "disk.vmdk"
    assert body["file_spec"]["source_type"] == "PUSH"
    assert "action=add" in vcenter_authed.calls[-1].request.url


def test_update_session_list_files(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        f"{BASE}/api/content/library/item/updatesession/file",
        json=[],
        status=200,
    )
    c.update_session_list_files(opts, "session-1")
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body == {"update_session_id": "session-1"}
    assert "action=list" in vcenter_authed.calls[-1].request.url


# -- OVF deploy -----------------------------------------------------------


def test_ovf_deploy(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        f"{BASE}/api/vcenter/ovf/library-item/item-1",
        json={"succeeded": True, "resource_id": {"type": "VirtualMachine", "id": "vm-99"}},
        status=200,
    )
    out = c.ovf_deploy(
        opts,
        "item-1",
        {"resource_pool_id": "rp-1", "folder_id": "f-1"},
        {"name": "vm-from-ovf", "accept_all_eula": True},
    )
    assert out["resource_id"]["id"] == "vm-99"
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body["target"]["resource_pool_id"] == "rp-1"
    assert body["deployment_spec"]["name"] == "vm-from-ovf"
    assert "action=deploy" in vcenter_authed.calls[-1].request.url


def test_ovf_filter(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        f"{BASE}/api/vcenter/ovf/library-item/item-1",
        json={"networks": ["VM Network"]},
        status=200,
    )
    c.ovf_filter(opts, "item-1", {"resource_pool_id": "rp-1"})
    assert "action=filter" in vcenter_authed.calls[-1].request.url


def test_ovf_create_from_vm(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        f"{BASE}/api/vcenter/ovf/library-item",
        json={"library_item_id": "item-new"},
        status=200,
    )
    c.ovf_create_from_vm(opts, "vm-1", {"name": "snapshot", "library": "lib-1"})
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body["source"] == {"type": "VirtualMachine", "id": "vm-1"}
    assert body["create_spec"]["library"] == "lib-1"
    assert "action=create_from_vm_template" in vcenter_authed.calls[-1].request.url


# -- VM template library items --------------------------------------------


def test_vm_template_get(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        f"{BASE}/api/vcenter/vm-template/library-items/item-1",
        json={"guest_OS": "RHEL_9_64"},
        status=200,
    )
    assert c.vm_template_get(opts, "item-1")["guest_OS"] == "RHEL_9_64"


def test_vm_template_get_or_none_404(opts, vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        f"{BASE}/api/vcenter/vm-template/library-items/missing",
        status=404,
    )
    assert c.vm_template_get_or_none(opts, "missing") is None


def test_vm_template_create(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        f"{BASE}/api/vcenter/vm-template/library-items",
        json="item-new",
        status=200,
    )
    out = c.vm_template_create(
        opts, {"name": "tpl", "library": "lib-1", "source_vm": "vm-1", "placement": {}}
    )
    assert out == "item-new"
    body = json.loads(vcenter_authed.calls[-1].request.body)
    assert body["spec"]["name"] == "tpl"


def test_vm_template_deploy(opts, vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        f"{BASE}/api/vcenter/vm-template/library-items/item-1",
        json="vm-99",
        status=200,
    )
    out = c.vm_template_deploy(opts, "item-1", {"name": "newvm", "placement": {}})
    assert out == "vm-99"
    assert "action=deploy" in vcenter_authed.calls[-1].request.url


def test_module_wrappers_delegate(opts, monkeypatch, vcenter_authed):
    """Smoke-test the execution module thin-wrapper layer."""
    from saltext.vcf.modules import vcf_vcenter_content_library as m

    monkeypatch.setattr(m, "__opts__", opts, raising=False)

    vcenter_authed.add(
        responses.PATCH, f"{BASE}/api/content/local-library/lib-1", json={}, status=200
    )
    vcenter_authed.add(
        responses.POST, f"{BASE}/api/content/subscribed-library/lib-2", json=None, status=200
    )
    vcenter_authed.add(
        responses.POST, f"{BASE}/api/content/library/item", json="item-99", status=200
    )
    m.update_local("lib-1", {"name": "x"})
    m.sync_subscribed("lib-2")
    assert m.create_item("lib-1", "x", "ovf") == "item-99"
