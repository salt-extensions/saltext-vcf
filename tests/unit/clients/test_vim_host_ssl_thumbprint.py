"""Tests for clients.vim_host_ssl_thumbprint."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from saltext.vmware.clients import vim_host_ssl_thumbprint


@pytest.fixture
def host_factory(monkeypatch):
    host = MagicMock()
    host.summary.config.sslThumbprint = "AA:BB:CC"
    host.name = "esx-1"
    monkeypatch.setattr(vim_host_ssl_thumbprint, "_host", lambda opts, h, profile=None: host)
    return host


def test_current_reads_summary(opts, host_factory):
    assert vim_host_ssl_thumbprint.current(opts, "esx-1") == "AA:BB:CC"


def test_fetch_returns_colon_separated_sha1():
    # Mock socket + ssl path; getpeercert(binary_form=True) returns DER bytes
    der = b"fakecertbytes"
    fake_ssock = MagicMock()
    fake_ssock.getpeercert.return_value = der
    fake_ssock.__enter__ = MagicMock(return_value=fake_ssock)
    fake_ssock.__exit__ = MagicMock(return_value=False)
    fake_ctx = MagicMock()
    fake_ctx.wrap_socket.return_value = fake_ssock
    fake_sock = MagicMock()
    fake_sock.__enter__ = MagicMock(return_value=fake_sock)
    fake_sock.__exit__ = MagicMock(return_value=False)
    with patch(
        "saltext.vmware.clients.vim_host_ssl_thumbprint.ssl.create_default_context",
        return_value=fake_ctx,
    ):
        with patch(
            "saltext.vmware.clients.vim_host_ssl_thumbprint.socket.create_connection",
            return_value=fake_sock,
        ):
            tp = vim_host_ssl_thumbprint.fetch("esx-1")
    # SHA-1 hex of b"fakecertbytes" — 40 chars → 20 colon-separated bytes
    assert tp.count(":") == 19
    assert all(len(b) == 2 for b in tp.split(":"))


def test_validate_matches(opts, host_factory):
    with patch(
        "saltext.vmware.clients.vim_host_ssl_thumbprint.fetch",
        return_value="AA:BB:CC",
    ):
        out = vim_host_ssl_thumbprint.validate(opts, "esx-1")
    assert out == {"current": "AA:BB:CC", "live": "AA:BB:CC", "match": True}


def test_validate_mismatch(opts, host_factory):
    with patch(
        "saltext.vmware.clients.vim_host_ssl_thumbprint.fetch",
        return_value="DD:EE:FF",
    ):
        out = vim_host_ssl_thumbprint.validate(opts, "esx-1")
    assert out["match"] is False


def test_validate_unreachable(opts, host_factory):
    with patch(
        "saltext.vmware.clients.vim_host_ssl_thumbprint.fetch",
        side_effect=OSError("connection refused"),
    ):
        out = vim_host_ssl_thumbprint.validate(opts, "esx-1")
    assert out["live"] is None
    assert out["match"] is False
