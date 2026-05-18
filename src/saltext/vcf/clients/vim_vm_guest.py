"""In-guest operations via VMware Tools (SOAP ``GuestOperationsManager``).

Two managers on ``ServiceContent.guestOperationsManager``:

* **ProcessManager** — start/list/terminate processes inside the guest
* **FileManager** — upload, download, list, delete, mkdir, move files

All operations require VMware Tools running in the guest plus per-call
``NamePasswordAuthentication`` credentials. File transfer uses signed
HTTPS URLs returned by the manager; the caller streams bytes there
directly. See :func:`upload_file` for details.
"""

import os
import ssl
import urllib.request

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _vm(opts, vm_id_or_name, profile=None):
    content = soap.content(opts, profile=profile)
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.VirtualMachine], True
    )
    try:
        for vm in container.view:
            if vm_id_or_name in (vm._moId, vm.name):  # noqa: SLF001
                return vm
    finally:
        container.Destroy()
    raise LookupError(f"VM {vm_id_or_name!r} not found")


def _guest_mgr(opts, profile=None):
    return soap.content(opts, profile=profile).guestOperationsManager


def _creds(username, password, interactive=False):
    return vim.vm.guest.NamePasswordAuthentication(
        username=username,
        password=password,
        interactiveSession=bool(interactive),
    )


# ---------------------------------------------------------------------------
# Processes
# ---------------------------------------------------------------------------


def run_command(
    opts,
    vm_id_or_name,
    program_path,
    arguments="",
    *,
    username,
    password,
    working_directory=None,
    env=None,
    profile=None,
):
    """Start *program_path* inside the guest.

    Returns the PID of the launched process. The call is fire-and-forget —
    use :func:`list_processes` to poll for completion / exit status.
    """
    vm = _vm(opts, vm_id_or_name, profile=profile)
    pm = _guest_mgr(opts, profile=profile).processManager
    spec = vim.vm.guest.ProcessManager.ProgramSpec(
        programPath=program_path,
        arguments=arguments,
    )
    if working_directory:
        spec.workingDirectory = working_directory
    if env:
        spec.envVariables = [f"{k}={v}" for k, v in env.items()]
    return pm.StartProgramInGuest(vm=vm, auth=_creds(username, password), spec=spec)


def list_processes(opts, vm_id_or_name, *, username, password, pids=None, profile=None):
    """List guest processes. Returns a list of ``{pid, name, owner, cmd_line,
    start_time, exit_code, end_time}`` dicts.

    When *pids* is provided, only those PIDs are reported (and entries with
    missing pids return ``None`` fields rather than a server-side error).
    """
    vm = _vm(opts, vm_id_or_name, profile=profile)
    pm = _guest_mgr(opts, profile=profile).processManager
    info = pm.ListProcessesInGuest(
        vm=vm,
        auth=_creds(username, password),
        pids=list(pids or []),
    )
    out = []
    for p in info or []:
        out.append(
            {
                "pid": p.pid,
                "name": p.name,
                "owner": p.owner,
                "cmd_line": p.cmdLine,
                "start_time": p.startTime.isoformat() if p.startTime else None,
                "exit_code": p.exitCode,
                "end_time": p.endTime.isoformat() if p.endTime else None,
            }
        )
    return out


def terminate_process(opts, vm_id_or_name, pid, *, username, password, profile=None):
    """Send a guest-OS terminate signal to *pid* (kill -9 on Linux)."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    pm = _guest_mgr(opts, profile=profile).processManager
    pm.TerminateProcessInGuest(vm=vm, auth=_creds(username, password), pid=int(pid))


def read_environment(opts, vm_id_or_name, *, username, password, names=None, profile=None):
    """Return the guest user's environment variables as a list of strings.

    When *names* is provided, only those keys are returned; otherwise the
    full environment is fetched.
    """
    vm = _vm(opts, vm_id_or_name, profile=profile)
    pm = _guest_mgr(opts, profile=profile).processManager
    return list(
        pm.ReadEnvironmentVariableInGuest(
            vm=vm, auth=_creds(username, password), names=list(names or [])
        )
        or []
    )


# ---------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------


def upload_file(
    opts,
    vm_id_or_name,
    src_path,
    dst_path,
    *,
    username,
    password,
    overwrite=True,
    permissions=0o644,
    verify_ssl=False,
    profile=None,
):
    """Upload a local file to *dst_path* inside the guest.

    The flow is:

    1. ``InitiateFileTransferToGuest`` returns a signed HTTPS URL
    2. HTTP PUT the file bytes to that URL

    *verify_ssl* defaults to False because the URL points back to the ESXi
    host the VM is running on; in many lab configs that's self-signed.
    """
    vm = _vm(opts, vm_id_or_name, profile=profile)
    fm = _guest_mgr(opts, profile=profile).fileManager
    file_size = os.path.getsize(src_path)
    file_attr = vim.vm.guest.FileManager.PosixFileAttributes(permissions=permissions)
    url = fm.InitiateFileTransferToGuest(
        vm=vm,
        auth=_creds(username, password),
        guestFilePath=dst_path,
        fileAttributes=file_attr,
        fileSize=int(file_size),
        overwrite=bool(overwrite),
    )
    ctx = None if verify_ssl else ssl._create_unverified_context()
    with open(src_path, "rb") as fh:
        request = urllib.request.Request(url, data=fh.read(), method="PUT")
        with urllib.request.urlopen(request, context=ctx) as resp:
            resp.read()
    return url


def download_file(
    opts,
    vm_id_or_name,
    src_path,
    dst_path,
    *,
    username,
    password,
    verify_ssl=False,
    profile=None,
):
    """Download *src_path* from the guest into a local *dst_path*."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    fm = _guest_mgr(opts, profile=profile).fileManager
    info = fm.InitiateFileTransferFromGuest(
        vm=vm, auth=_creds(username, password), guestFilePath=src_path
    )
    ctx = None if verify_ssl else ssl._create_unverified_context()
    with urllib.request.urlopen(info.url, context=ctx) as resp:
        body = resp.read()
    with open(dst_path, "wb") as fh:
        fh.write(body)
    return info.size


def list_files(
    opts,
    vm_id_or_name,
    path,
    *,
    username,
    password,
    pattern=None,
    profile=None,
):
    """List directory entries at *path* in the guest."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    fm = _guest_mgr(opts, profile=profile).fileManager
    info = fm.ListFilesInGuest(
        vm=vm,
        auth=_creds(username, password),
        filePath=path,
        matchPattern=pattern,
    )
    out = []
    for entry in info.files or []:
        out.append(
            {
                "path": entry.path,
                "type": str(entry.type),
                "size": entry.size,
                "modification_time": entry.modification.isoformat() if entry.modification else None,
            }
        )
    return out


def delete_file(opts, vm_id_or_name, path, *, username, password, profile=None):
    vm = _vm(opts, vm_id_or_name, profile=profile)
    fm = _guest_mgr(opts, profile=profile).fileManager
    fm.DeleteFileInGuest(vm=vm, auth=_creds(username, password), filePath=path)


def make_directory(
    opts,
    vm_id_or_name,
    path,
    *,
    username,
    password,
    create_parents=False,
    profile=None,
):
    """Create a directory inside the guest; *create_parents* mimics ``mkdir -p``."""
    vm = _vm(opts, vm_id_or_name, profile=profile)
    fm = _guest_mgr(opts, profile=profile).fileManager
    fm.MakeDirectoryInGuest(
        vm=vm,
        auth=_creds(username, password),
        directoryPath=path,
        createParentDirectories=bool(create_parents),
    )


def delete_directory(
    opts,
    vm_id_or_name,
    path,
    *,
    username,
    password,
    recursive=False,
    profile=None,
):
    vm = _vm(opts, vm_id_or_name, profile=profile)
    fm = _guest_mgr(opts, profile=profile).fileManager
    fm.DeleteDirectoryInGuest(
        vm=vm,
        auth=_creds(username, password),
        directoryPath=path,
        recursive=bool(recursive),
    )


def move_file(
    opts,
    vm_id_or_name,
    src_path,
    dst_path,
    *,
    username,
    password,
    overwrite=False,
    profile=None,
):
    vm = _vm(opts, vm_id_or_name, profile=profile)
    fm = _guest_mgr(opts, profile=profile).fileManager
    fm.MoveFileInGuest(
        vm=vm,
        auth=_creds(username, password),
        srcFilePath=src_path,
        dstFilePath=dst_path,
        overwrite=bool(overwrite),
    )
