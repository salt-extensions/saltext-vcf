"""Tests for modules.vcf_esxi_vlcm."""

import pytest
import responses

from saltext.vcf.modules import vcf_esxi_vlcm as mod


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(mod, "__opts__", opts, raising=False)


def test_online_depot_list(vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/esx/settings/depots/online",
        json=[],
        status=200,
    )
    assert mod.online_depot_list() == []


def test_desired_image_get(vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/esx/settings/clusters/c1/software",
        json={"base_image": {"version": "1.0"}},
        status=200,
    )
    assert mod.desired_image_get("c1") == {"base_image": {"version": "1.0"}}


def test_compliance_scan(vcenter_authed):
    vcenter_authed.add(
        responses.POST,
        "https://vc.test/api/esx/settings/clusters/c1/software",
        json="task-1",
        status=200,
    )
    assert mod.compliance_scan("c1") == "task-1"
    assert "action=scan" in vcenter_authed.calls[-1].request.url


def test_wait_for_task(vcenter_authed):
    vcenter_authed.add(
        responses.GET,
        "https://vc.test/api/cis/tasks/task-1",
        json={"status": "SUCCEEDED"},
        status=200,
    )
    task = mod.wait_for_task("task-1", timeout=5, poll_interval=0)
    assert task["status"] == "SUCCEEDED"
