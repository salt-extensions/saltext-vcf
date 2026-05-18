"""Framework-interface tests for resources.vcf_vm."""

import pytest
import responses

from saltext.vcf.resources import vcf_vm as vm

KEY = vm.CONTEXT_KEY


def _inject(monkeypatch, resource_id, framework_opts):
    """Mirror the framework's init() into a manual context."""
    tree = framework_opts["pillar"]["resources"]
    monkeypatch.setattr(vm, "__resource__", {"id": resource_id}, raising=False)
    monkeypatch.setattr(
        vm,
        "__context__",
        {
            KEY: {
                "initialized": True,
                "instances": tree["vcf_vm"]["instances"],
                "vcenter_instances": tree["vcenter"]["instances"],
            }
        },
        raising=False,
    )


def test_discover_returns_vm_ids(framework_opts):
    assert sorted(vm.discover(framework_opts)) == ["orphan", "web-01", "web-02"]


def test_init_initialized_shutdown(monkeypatch, framework_opts):
    ctx = {}
    monkeypatch.setattr(vm, "__context__", ctx, raising=False)
    assert vm.initialized() is False
    vm.init(framework_opts)
    assert vm.initialized() is True
    assert "web-01" in ctx[KEY]["instances"]
    assert "mgmt-vc" in ctx[KEY]["vcenter_instances"]
    vm.shutdown(framework_opts)
    assert KEY not in ctx


def test_grains_static_fields_only_on_unreachable_vcenter(
    monkeypatch, framework_opts, mocked_responses
):
    _inject(monkeypatch, "web-01", framework_opts)
    mocked_responses.add(responses.POST, "https://vc.test/api/session", status=503)
    g = vm.grains()
    assert g["resource_type"] == "vcf_vm"
    assert g["resource_id"] == "web-01"
    assert g["vcenter"] == "mgmt-vc"
    assert g["moid"] == "vm-100"
    # labels are promoted as top-level grains for targeting
    assert g["tier"] == "production"
    assert g["app"] == "web"
    # live fields absent on session failure
    assert "name" not in g


def test_grains_includes_live_vcenter_fields(monkeypatch, framework_opts, vcenter_authed):
    _inject(monkeypatch, "web-01", framework_opts)
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/vm/vm-100",
        json={
            "name": "web-prod-01",
            "power_state": "POWERED_ON",
            "cpu_count": 4,
            "memory_size_MiB": 8192,
        },
        status=200,
    )
    g = vm.grains()
    assert g["name"] == "web-prod-01"
    assert g["power_state"] == "POWERED_ON"
    assert g["cpu_count"] == 4
    assert g["memory_size_MiB"] == 8192
    # static still present
    assert g["tier"] == "production"


def test_ping_ok(monkeypatch, framework_opts, mocked_responses):
    _inject(monkeypatch, "web-01", framework_opts)
    mocked_responses.add(responses.POST, "https://vc.test/api/session", json="token", status=200)
    assert vm.ping() is True


def test_ping_accepts_201(monkeypatch, framework_opts, mocked_responses):
    _inject(monkeypatch, "web-01", framework_opts)
    mocked_responses.add(responses.POST, "https://vc.test/api/session", json="token", status=201)
    assert vm.ping() is True


def test_ping_unreachable(monkeypatch, framework_opts, mocked_responses):
    _inject(monkeypatch, "web-01", framework_opts)
    mocked_responses.add(responses.POST, "https://vc.test/api/session", status=401)
    assert vm.ping() is False


def test_ping_orphan_vm_with_missing_vcenter(monkeypatch, framework_opts):
    _inject(monkeypatch, "orphan", framework_opts)
    assert vm.ping() is False


def test_info_routes_to_correct_vcenter(monkeypatch, framework_opts, vcenter_authed):
    _inject(monkeypatch, "web-02", framework_opts)
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/vm/vm-101",
        json={"name": "web-prod-02", "power_state": "POWERED_OFF"},
        status=200,
    )
    record = vm.info()
    assert record["name"] == "web-prod-02"


def test_power_state_returns_string(monkeypatch, framework_opts, vcenter_authed):
    _inject(monkeypatch, "web-01", framework_opts)
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/vm/vm-100",
        json={"power_state": "POWERED_ON"},
        status=200,
    )
    assert vm.power_state() == "POWERED_ON"


def test_power_on_off_reset(monkeypatch, framework_opts, vcenter_authed):
    _inject(monkeypatch, "web-01", framework_opts)
    for _action in ("start", "stop", "reset"):
        vcenter_authed.add(
            responses.POST,
            "https://vc.test/api/vcenter/vm/vm-100/power",
            json={},
            status=200,
        )
    vm.power_on()
    vm.power_off()
    vm.reset()
    # Verify the action query string was forwarded
    actions = [c.request.url.split("action=")[-1] for c in vcenter_authed.calls[-3:]]
    assert set(actions) == {"start", "stop", "reset"}


def test_tag_list_assigned(monkeypatch, framework_opts, vcenter_authed):
    _inject(monkeypatch, "web-01", framework_opts)
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/cis/tagging/tag-association",
        json=["urn:vmomi:Tag:prod"],
        status=200,
    )
    result = vm.tag_list_assigned()
    assert "urn:vmomi:Tag:prod" in result


def test_tag_assign(monkeypatch, framework_opts, vcenter_authed):
    _inject(monkeypatch, "web-01", framework_opts)
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/cis/tagging/tag-association/urn:vmomi:Tag:prod",
        json={},
        status=200,
    )
    vm.tag_assign("urn:vmomi:Tag:prod")
    call = vcenter_authed.calls[-1]
    assert "action=attach" in call.request.url


def test_orphan_vm_info_raises_useful_error(monkeypatch, framework_opts):
    _inject(monkeypatch, "orphan", framework_opts)
    with pytest.raises(ValueError, match="missing-vc"):
        vm.info()


def test_snapshot_create_delegates_to_soap(monkeypatch, framework_opts):
    _inject(monkeypatch, "web-01", framework_opts)
    seen = {}

    def stub(opts, moid, name, **kwargs):
        seen["moid"] = moid
        seen["name"] = name
        seen.update(kwargs)
        return "task-1"

    monkeypatch.setattr("saltext.vcf.resources.vcf_vm.vim_vm_snapshot.create", stub)
    result = vm.snapshot_create("baseline", description="x", memory=True, quiesce=False)
    assert result == "task-1"
    assert seen["moid"] == "vm-100"
    assert seen["name"] == "baseline"
    assert seen["description"] == "x"
    assert seen["memory"] is True


def test_snapshot_list_delegates(monkeypatch, framework_opts):
    _inject(monkeypatch, "web-01", framework_opts)
    monkeypatch.setattr(
        "saltext.vcf.resources.vcf_vm.vim_vm_snapshot.list_",
        lambda opts, moid: [{"id": "snap-1", "name": "baseline"}],
    )
    result = vm.snapshot_list()
    assert result[0]["name"] == "baseline"
