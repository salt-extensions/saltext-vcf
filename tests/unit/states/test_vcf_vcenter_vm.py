from saltext.vcf.states import vcf_vcenter_vm


def test_deployed_noops_when_vm_exists(monkeypatch):
    monkeypatch.setattr(
        vcf_vcenter_vm.r, "get_by_name", lambda opts, name, profile=None: {"vm": "vm-1"}
    )
    monkeypatch.setattr(vcf_vcenter_vm, "__opts__", {"test": False}, raising=False)

    ret = vcf_vcenter_vm.deployed("poc", {"template": "tmpl"})

    assert ret["result"] is True
    assert ret["changes"] == {}


def test_deployed_submits_when_missing(monkeypatch):
    monkeypatch.setattr(vcf_vcenter_vm.r, "get_by_name", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        vcf_vcenter_vm.r,
        "deploy",
        lambda opts, name, spec, profile=None: {"task": "task-1"},
    )
    monkeypatch.setattr(vcf_vcenter_vm, "__opts__", {"test": False}, raising=False)

    ret = vcf_vcenter_vm.deployed("poc", {"template": "tmpl"})

    assert ret["changes"]["task"] == "task-1"


def test_reachable_fails_on_timeout(monkeypatch):
    monkeypatch.setattr(vcf_vcenter_vm.r, "wait_reachable", lambda *args, **kwargs: False)
    monkeypatch.setattr(vcf_vcenter_vm, "__opts__", {"test": False}, raising=False)

    ret = vcf_vcenter_vm.reachable("poc", "10.0.0.10", timeout_sec=1)

    assert ret["result"] is False
