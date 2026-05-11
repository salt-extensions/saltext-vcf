"""Tests for clients.vim_extension."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from saltext.vmware.clients import vim_extension


@pytest.fixture
def fake_ext():
    e = MagicMock()
    e.key = "com.example.salt"
    e.version = "1.0.0"
    e.company = "Example"
    e.description.label = "Salt extension"
    e.lastHeartbeatTime = None
    e.server = []
    e.client = []
    return e


def test_list_returns_dicts(opts, fake_ext):
    em = MagicMock()
    em.extensionList = [fake_ext]
    with patch("saltext.vmware.clients.vim_extension.soap.extension_manager", return_value=em):
        result = vim_extension.list_(opts)
    assert result[0]["key"] == "com.example.salt"
    assert result[0]["version"] == "1.0.0"


def test_get_found(opts, fake_ext):
    em = MagicMock()
    em.FindExtension.return_value = fake_ext
    with patch("saltext.vmware.clients.vim_extension.soap.extension_manager", return_value=em):
        result = vim_extension.get(opts, "com.example.salt")
    assert result["key"] == "com.example.salt"


def test_get_missing(opts):
    em = MagicMock()
    em.FindExtension.return_value = None
    with patch("saltext.vmware.clients.vim_extension.soap.extension_manager", return_value=em):
        assert vim_extension.get(opts, "missing") is None


def test_register_calls_registerextension(opts):
    em = MagicMock()
    with patch("saltext.vmware.clients.vim_extension.soap.extension_manager", return_value=em):
        result = vim_extension.register(opts, "com.example.salt", "1.0.0", "Salt", "Example")
    assert result == "com.example.salt"
    em.RegisterExtension.assert_called_once()


def test_unregister(opts):
    em = MagicMock()
    with patch("saltext.vmware.clients.vim_extension.soap.extension_manager", return_value=em):
        vim_extension.unregister(opts, "com.example.salt")
    em.UnregisterExtension.assert_called_once_with(extensionKey="com.example.salt")


def test_update_raises_when_missing(opts):
    em = MagicMock()
    em.FindExtension.return_value = None
    with patch("saltext.vmware.clients.vim_extension.soap.extension_manager", return_value=em):
        with pytest.raises(LookupError):
            vim_extension.update(opts, "com.example.salt", version="2.0.0")
