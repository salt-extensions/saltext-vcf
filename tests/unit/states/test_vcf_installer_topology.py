from saltext.vcf.states import vcf_installer_topology


def test_valid_state_succeeds(monkeypatch):
    monkeypatch.setattr(
        vcf_installer_topology.m,
        "validate",
        lambda spec: {"valid": True, "errors": [], "warnings": []},
    )

    ret = vcf_installer_topology.valid("vcf-mgmt", spec={"bringup_spec": {}})

    assert ret["result"] is True
    assert ret["changes"] == {}
    assert ret["comment"] == "topology valid"


def test_valid_state_fails_with_validation_errors(monkeypatch):
    monkeypatch.setattr(
        vcf_installer_topology.m,
        "validate",
        lambda spec: {"valid": False, "errors": ["missing hostSpecs"], "warnings": []},
    )

    ret = vcf_installer_topology.valid("vcf-mgmt", spec={})

    assert ret["result"] is False
    assert ret["comment"] == "missing hostSpecs"
