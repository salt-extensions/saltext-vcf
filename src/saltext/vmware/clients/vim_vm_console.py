"""VM console operations: screenshot + sendkey via ``VirtualMachine`` methods."""

from pyVmomi import vim

from saltext.vmware.clients.vim_vm import _vm


def screenshot(opts, vm_id_or_name, profile=None):
    """Capture a console screenshot. Returns vim.Task moId.

    On success, ``task.info.result`` is a datastore path string like
    ``[ds1] my-vm/screenshot.png``. Call ``vim_datastore_file.download``
    to pull the bytes locally.
    """
    vm = _vm(opts, vm_id_or_name, profile=profile)
    task = vm.CreateScreenshot_Task()
    return task._moId  # noqa: SLF001


# USB HID scan codes for common keys (subset — extend as needed).
# Reference: USB HID Usage Tables, Keyboard/Keypad page (0x07).
KEY_CODES = {
    "a": 0x04,
    "b": 0x05,
    "c": 0x06,
    "d": 0x07,
    "e": 0x08,
    "f": 0x09,
    "g": 0x0A,
    "h": 0x0B,
    "i": 0x0C,
    "j": 0x0D,
    "k": 0x0E,
    "l": 0x0F,
    "m": 0x10,
    "n": 0x11,
    "o": 0x12,
    "p": 0x13,
    "q": 0x14,
    "r": 0x15,
    "s": 0x16,
    "t": 0x17,
    "u": 0x18,
    "v": 0x19,
    "w": 0x1A,
    "x": 0x1B,
    "y": 0x1C,
    "z": 0x1D,
    "1": 0x1E,
    "2": 0x1F,
    "3": 0x20,
    "4": 0x21,
    "5": 0x22,
    "6": 0x23,
    "7": 0x24,
    "8": 0x25,
    "9": 0x26,
    "0": 0x27,
    "enter": 0x28,
    "escape": 0x29,
    "backspace": 0x2A,
    "tab": 0x2B,
    "space": 0x2C,
    "f1": 0x3A,
    "f2": 0x3B,
    "f3": 0x3C,
    "f4": 0x3D,
    "f5": 0x3E,
    "f6": 0x3F,
    "f7": 0x40,
    "f8": 0x41,
    "f9": 0x42,
    "f10": 0x43,
    "f11": 0x44,
    "f12": 0x45,
    "right": 0x4F,
    "left": 0x50,
    "down": 0x51,
    "up": 0x52,
}


def _to_hid(code):
    if isinstance(code, int):
        return code
    if code in KEY_CODES:
        return KEY_CODES[code]
    if code.startswith("0x"):
        return int(code, 16)
    raise ValueError(f"unknown key code {code!r}")


def send_keys(opts, vm_id_or_name, keys, profile=None):
    """Send a sequence of HID scan codes to the VM console.

    *keys* — list of key names (``"enter"``, ``"f2"``, ``"a"``) or HID ints.
    Returns the number of keys successfully queued.
    """
    vm = _vm(opts, vm_id_or_name, profile=profile)
    key_events = []
    for k in keys:
        code = _to_hid(k)
        # USB HID scan code, formatted as required by PutUsbScanCodes:
        # bits 16-31 = scancode << 16
        usage = (code << 16) | 0x0007
        event = vim.UsbScanCodeSpecKeyEvent(usbHidCode=usage)
        key_events.append(event)
    spec = vim.UsbScanCodeSpec(keyEvents=key_events)
    return int(vm.PutUsbScanCodes(spec=spec))
