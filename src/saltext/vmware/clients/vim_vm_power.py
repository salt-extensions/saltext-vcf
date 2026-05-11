"""VM power lifecycle via SOAP (``vim.VirtualMachine.Power*Task`` + guest variants).

REST ``/api/vcenter/vm/{id}/power`` covers the basics, but several common ops
(reset, standby_guest, hard shutdown vs graceful tools-shutdown) want the SOAP
surface — and SOAP returns rich task references the caller can poll.

Asynchronous ops return the task moid; guest ops (``ShutdownGuest`` etc.) are
fire-and-forget commands without a task and return ``True``.
"""

from pyVmomi import vim

from saltext.vmware.clients.vim_vm import _find_by_type
from saltext.vmware.clients.vim_vm import _vm


def get_power_state(opts, vm_id_or_name, profile=None):
    """Return runtime power state: ``poweredOn`` / ``poweredOff`` / ``suspended``."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    return str(vm.runtime.powerState)


def power_on(opts, vm_id_or_name, host=None, profile=None):
    """Hard power-on. If *host* is set, schedules on that target host."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    host_ref = None
    if host is not None:
        host_ref = _find_by_type(opts, vim.HostSystem, host, profile=profile)
    task = vm.PowerOnVM_Task(host=host_ref)
    return task._moId  # noqa: SLF001


def power_off(opts, vm_id_or_name, profile=None):
    """Hard power-off (yank cord)."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    task = vm.PowerOffVM_Task()
    return task._moId  # noqa: SLF001


def shutdown_guest(opts, vm_id_or_name, profile=None):
    """Send a graceful ACPI shutdown via VMware Tools. Synchronous (no task)."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    vm.ShutdownGuest()
    return True


def reboot_guest(opts, vm_id_or_name, profile=None):
    """Send a graceful reboot via VMware Tools. Synchronous (no task)."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    vm.RebootGuest()
    return True


def standby_guest(opts, vm_id_or_name, profile=None):
    """Send a standby/suspend command via VMware Tools. Synchronous (no task)."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    vm.StandbyGuest()
    return True


def reset(opts, vm_id_or_name, profile=None):
    """Hard reset."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    task = vm.ResetVM_Task()
    return task._moId  # noqa: SLF001


def suspend(opts, vm_id_or_name, profile=None):
    """Suspend (saves state to a .vmss file)."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    task = vm.SuspendVM_Task()
    return task._moId  # noqa: SLF001
