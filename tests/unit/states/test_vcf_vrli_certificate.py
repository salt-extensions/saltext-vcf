"""Tests for states.vcf_vrli_certificate."""

import subprocess
import tempfile

import pytest

from saltext.vcf.clients import vrli_certificate as c
from saltext.vcf.states import vcf_vrli_certificate as st


@pytest.fixture(autouse=True)
def inject_opts(monkeypatch, opts):
    monkeypatch.setattr(st, "__opts__", opts, raising=False)


def _mkcert():
    """Generate a throwaway self-signed cert and return (pem, key, serial_lc_hex)."""
    with (
        tempfile.NamedTemporaryFile(suffix=".key") as key_f,
        tempfile.NamedTemporaryFile(suffix=".crt") as crt_f,
    ):
        subprocess.check_call(
            [
                "openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-keyout",
                key_f.name,
                "-out",
                crt_f.name,
                "-days",
                "1",
                "-subj",
                "/CN=vrli-test",
            ],
            stderr=subprocess.DEVNULL,
        )
        with open(crt_f.name, encoding="utf-8") as fh:
            cert_pem = fh.read()
        with open(key_f.name, encoding="utf-8") as fh:
            key_pem = fh.read()
    # Extract serial with openssl for cross-checking.
    proc = subprocess.run(
        ["openssl", "x509", "-noout", "-serial"],
        input=cert_pem,
        text=True,
        capture_output=True,
        check=True,
    )
    serial_hex = proc.stdout.strip().split("=", 1)[1].lower().lstrip("0") or "0"
    return cert_pem, key_pem, serial_hex


@pytest.fixture
def certmat():
    return _mkcert()


@pytest.fixture
def stub(monkeypatch):
    state = {"current": None, "install_calls": []}
    monkeypatch.setattr(c, "get", lambda o, profile=None: state["current"])
    monkeypatch.setattr(
        c,
        "install",
        lambda o, cert, key, chain_pem=None, profile=None: state["install_calls"].append(
            {"cert": cert, "key": key, "chain": chain_pem}
        ),
    )
    return state


def test_serial_from_pem_parses_ok(certmat):
    cert, _key, serial = certmat
    parsed = st._serial_from_pem(cert)
    assert parsed.lower().lstrip("0") == serial


def test_certificate_present_installs_when_none(stub, certmat):
    cert, key, serial = certmat
    ret = st.certificate_present("c", cert=cert, key=key)
    assert stub["install_calls"]
    assert ret["changes"]["serialNum"]["new"] == serial


def test_certificate_present_idempotent(stub, certmat):
    cert, key, serial = certmat
    stub["current"] = {"serialNum": serial}
    ret = st.certificate_present("c", cert=cert, key=key)
    assert ret["changes"] == {}
    assert stub["install_calls"] == []


def test_certificate_present_test_mode(stub, certmat, opts):
    opts["test"] = True
    cert, key, _ = certmat
    ret = st.certificate_present("c", cert=cert, key=key)
    assert ret["result"] is None
    assert stub["install_calls"] == []
