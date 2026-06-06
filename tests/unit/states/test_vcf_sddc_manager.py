from saltext.vcf.states import vcf_sddc_manager


def test_ready_succeeds_when_endpoint_returns_info(monkeypatch):
    monkeypatch.setattr(
        vcf_sddc_manager.r, "get_or_none", lambda opts, profile=None: {"id": "sddc"}
    )
    monkeypatch.setattr(vcf_sddc_manager, "__opts__", {"test": False}, raising=False)

    ret = vcf_sddc_manager.ready("sddc.test")

    assert ret["result"] is True
    assert "reachable" in ret["comment"]


def test_ready_fails_when_endpoint_unreachable(monkeypatch):
    monkeypatch.setattr(vcf_sddc_manager.r, "get_or_none", lambda opts, profile=None: None)
    monkeypatch.setattr(vcf_sddc_manager, "__opts__", {"test": False}, raising=False)

    ret = vcf_sddc_manager.ready("sddc.test")

    assert ret["result"] is False
    assert "not reachable" in ret["comment"]
