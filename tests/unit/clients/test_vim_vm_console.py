"""Tests for clients.vim_vm_console (screenshot, send_keys, MKS ticket)."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from pyVmomi import vim

from saltext.vcf.clients import vim_vm_console


def _fake_vm():
    vm = MagicMock()
    vm.name = "web-01"
    vm.CreateScreenshot_Task.return_value = MagicMock(_moId="task-shot-1")
    vm.PutUsbScanCodes.return_value = 2
    return vm


def test_ticket_returns_dict(opts):
    vm = _fake_vm()
    ticket = MagicMock()
    ticket.host = "10.0.0.5"
    ticket.port = 443
    ticket.sslThumbprint = "AB:CD"
    ticket.ticket = "secret-ticket"
    vm.AcquireTicket.return_value = ticket
    with patch.object(vim_vm_console, "_vm", return_value=vm):
        out = vim_vm_console.ticket(opts, "web-01", "webmks")
    assert out["host"] == "10.0.0.5"
    assert out["port"] == 443
    assert out["ssl_thumbprint"] == "AB:CD"
    assert out["ticket"] == "secret-ticket"
    vm.AcquireTicket.assert_called_once_with(vim.VirtualMachine.TicketType.webmks)


def test_ticket_rejects_unknown_type(opts):
    vm = _fake_vm()
    with patch.object(vim_vm_console, "_vm", return_value=vm):
        with pytest.raises(ValueError):
            vim_vm_console.ticket(opts, "web-01", "bogus")
    vm.AcquireTicket.assert_not_called()


def test_screenshot_returns_task(opts):
    vm = _fake_vm()
    with patch.object(vim_vm_console, "_vm", return_value=vm):
        assert vim_vm_console.screenshot(opts, "web-01") == "task-shot-1"


def test_send_keys_queues_codes(opts):
    vm = _fake_vm()
    with patch.object(vim_vm_console, "_vm", return_value=vm):
        assert vim_vm_console.send_keys(opts, "web-01", ["f2", "enter"]) == 2
    spec = vm.PutUsbScanCodes.call_args.kwargs["spec"]
    assert len(spec.keyEvents) == 2
