"""Framework-interface tests for resources.vmsp."""

import responses

from saltext.vcf.resources import vmsp as vm

KEY = vm.CONTEXT_KEY
COMPONENTS_URL = "https://vmsp.test/api/v1/components"


def _vsp(network=None, logs=None):
    return {
        "components": [
            {
                "id": "comp-vsp-1",
                "name": "vsp",
                "spec": {"configuration": {"network": network or {}, "logs": logs or {}}},
            }
        ]
    }


def test_discover(framework_opts):
    assert vm.discover(framework_opts) == ["vcf-vmsp"]


def test_init_initialized_shutdown(monkeypatch, framework_opts):
    monkeypatch.setattr(vm, "__context__", {}, raising=False)
    assert vm.initialized() is False
    vm.init(framework_opts)
    assert vm.initialized() is True
    vm.shutdown(framework_opts)
    assert vm.initialized() is False


def test_ping_ok(inject_resource_dunders, framework_opts, mocked_responses):
    instances = framework_opts["pillar"]["resources"]["vmsp"]["instances"]
    inject_resource_dunders(vm, "vcf-vmsp", KEY, instances)
    mocked_responses.add(
        responses.POST,
        "https://vmsp.test/api/v1/identity/token",
        json={"access_token": "t"},
        status=200,
    )
    assert vm.ping() is True


def test_ntp_get_routed(inject_resource_dunders, framework_opts, vmsp_authed):
    instances = framework_opts["pillar"]["resources"]["vmsp"]["instances"]
    inject_resource_dunders(vm, "vcf-vmsp", KEY, instances)
    vmsp_authed.add(responses.GET, COMPONENTS_URL, json=_vsp(network={"ntpServers": ["10.0.0.250"]}), status=200)
    assert vm.ntp_get() == {"servers": ["10.0.0.250"]}
