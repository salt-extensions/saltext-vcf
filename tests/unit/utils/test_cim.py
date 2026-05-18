"""Tests for saltext.vcf.utils.cim (pywbem wrapper)."""

from unittest.mock import patch

from saltext.vcf.utils import cim


def test_get_config_inherits_esxi_pillar(opts):
    cfg = cim.get_config(opts)
    assert cfg["host"] == "esxi.test"
    assert cfg["username"] == "root"
    assert cfg["cim_port"] == 5989


def test_get_config_respects_custom_port(opts):
    opts["pillar"]["saltext.vcf"]["esxi"]["cim_port"] = 5988
    cfg = cim.get_config(opts)
    assert cfg["cim_port"] == 5988


def test_get_connection_caches(opts):
    with patch(
        "saltext.vcf.utils.cim.pywbem.WBEMConnection"
    ) as Conn:  # pylint: disable=invalid-name
        Conn.return_value = object()
        c1 = cim.get_connection(opts)
        c2 = cim.get_connection(opts)
    assert c1 is c2
    assert Conn.call_count == 1


def test_get_connection_passes_url_and_creds(opts):
    with patch(
        "saltext.vcf.utils.cim.pywbem.WBEMConnection"
    ) as Conn:  # pylint: disable=invalid-name
        cim.get_connection(opts)
    args, kwargs = Conn.call_args
    assert args[0] == "https://esxi.test:5989"
    assert args[1] == ("root", "p")
    assert kwargs["no_verification"] is True


def test_invalidate_clears_cache(opts):
    with patch(
        "saltext.vcf.utils.cim.pywbem.WBEMConnection"
    ) as Conn:  # pylint: disable=invalid-name
        Conn.return_value = object()
        cim.get_connection(opts)
        assert cim._CONN_CACHE
        cim.invalidate_connection(opts)
        assert not cim._CONN_CACHE
