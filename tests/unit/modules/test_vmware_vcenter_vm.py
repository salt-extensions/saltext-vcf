"""Tests for modules.vmware_vcenter_vm."""

import pytest
import responses

from saltext.vmware.modules import vmware_vcenter_vm as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_list(vcenter_authed):
    vcenter_authed.add(responses.GET, "https://vc.test/api/vcenter/vm", json=[], status=200)
    assert mod.list_() == []


def test_get(vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/vcenter/vm/vm-1",
        json={"power_state": "POWERED_OFF"},
        status=200,
    )
    assert mod.get("vm-1") == {"power_state": "POWERED_OFF"}


@pytest.mark.parametrize(
    "fn,action",
    [
        ("power_on", "start"),
        ("power_off", "stop"),
        ("reset", "reset"),
    ],
)
def test_power_actions(vcenter_authed, fn, action):
    vcenter_authed.add(responses.POST, "https://vc.test/api/vcenter/vm/vm-1/power", status=204)
    getattr(mod, fn)("vm-1")
    assert f"action={action}" in vcenter_authed.calls[-1].request.url
