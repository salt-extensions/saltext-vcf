"""Execution module for VM console (screenshot, sendkey)."""

from saltext.vcf.clients import vim_vm_console as c

__virtualname__ = "vcf_vim_vm_console"


def __virtual__():
    return __virtualname__


def screenshot(vm, profile=None):
    """Capture a console screenshot. Returns task moId; result is a datastore path.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_console.screenshot <vm>
    """
    return c.screenshot(__opts__, vm, profile=profile)


def send_keys(vm, keys, profile=None):
    """Send a sequence of keys to *vm*'s console.

    *keys* is a list of key names (``enter``, ``f2``, ``a``, etc.) or HID ints.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_vm_console.send_keys <vm> '[f2]'
    """
    return c.send_keys(__opts__, vm, keys, profile=profile)
