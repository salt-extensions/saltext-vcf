from saltext.vcf.states import vcf_nsx_transport_zone


def test_present_noops_when_zone_exists(monkeypatch):
    monkeypatch.setattr(
        vcf_nsx_transport_zone.r,
        "get_by_name",
        lambda opts, name, profile=None: {"id": "tz-1", "transport_type": "OVERLAY"},
    )
    monkeypatch.setattr(vcf_nsx_transport_zone, "__opts__", {"test": False}, raising=False)

    ret = vcf_nsx_transport_zone.present("overlay-tz", "OVERLAY")

    assert ret["result"] is True
    assert ret["changes"] == {}


def test_present_creates_missing_zone(monkeypatch):
    monkeypatch.setattr(vcf_nsx_transport_zone.r, "get_by_name", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        vcf_nsx_transport_zone.r,
        "create",
        lambda opts, name, zone_type, profile=None, **spec: {"id": "tz-1"},
    )
    monkeypatch.setattr(vcf_nsx_transport_zone, "__opts__", {"test": False}, raising=False)

    ret = vcf_nsx_transport_zone.present("overlay-tz", "OVERLAY")

    assert ret["changes"] == {"new": "tz-1"}


def test_present_fails_on_type_mismatch(monkeypatch):
    monkeypatch.setattr(
        vcf_nsx_transport_zone.r,
        "get_by_name",
        lambda opts, name, profile=None: {"id": "tz-1", "transport_type": "VLAN"},
    )
    monkeypatch.setattr(vcf_nsx_transport_zone, "__opts__", {"test": False}, raising=False)

    ret = vcf_nsx_transport_zone.present("overlay-tz", "OVERLAY")

    assert ret["result"] is False
    assert "expected" in ret["comment"]
