"""Execution module for in-guest VM operations (SOAP via VMware Tools)."""

from saltext.vmware.clients import vim_vm_guest as c

__virtualname__ = "vmware_vim_vm_guest"


def __virtual__():
    return __virtualname__


# ---------- processes ----------


def run_command(
    vm,
    program_path,
    arguments="",
    username=None,
    password=None,
    working_directory=None,
    env=None,
    profile=None,
):
    """Start a program inside the guest, return its PID.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_guest.run_command vm-100 /bin/echo "hello" username=root password='<pw>'
    """
    return c.run_command(
        __opts__,
        vm,
        program_path,
        arguments=arguments,
        username=username,
        password=password,
        working_directory=working_directory,
        env=env,
        profile=profile,
    )


def list_processes(vm, username=None, password=None, pids=None, profile=None):
    """List processes in the guest (optionally filtered to *pids*).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_guest.list_processes vm-100 username=root password='<pw>'
    """
    return c.list_processes(
        __opts__, vm, username=username, password=password, pids=pids, profile=profile
    )


def terminate_process(vm, pid, username=None, password=None, profile=None):
    """Kill a process inside the guest.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_guest.terminate_process vm-100 1234 username=root password='<pw>'
    """
    return c.terminate_process(
        __opts__, vm, pid, username=username, password=password, profile=profile
    )


def read_environment(vm, username=None, password=None, names=None, profile=None):
    """Read the guest user's environment variables.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_guest.read_environment vm-100 username=root password='<pw>' names='["PATH"]'
    """
    return c.read_environment(
        __opts__,
        vm,
        username=username,
        password=password,
        names=names,
        profile=profile,
    )


# ---------- files ----------


def upload_file(
    vm,
    src_path,
    dst_path,
    username=None,
    password=None,
    overwrite=True,
    permissions=0o644,
    verify_ssl=False,
    profile=None,
):
    """Upload a local file to the guest.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_guest.upload_file vm-100 /tmp/local.sh /root/remote.sh username=root password='<pw>'
    """
    return c.upload_file(
        __opts__,
        vm,
        src_path,
        dst_path,
        username=username,
        password=password,
        overwrite=overwrite,
        permissions=permissions,
        verify_ssl=verify_ssl,
        profile=profile,
    )


def download_file(
    vm,
    src_path,
    dst_path,
    username=None,
    password=None,
    verify_ssl=False,
    profile=None,
):
    """Download a file from the guest.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_guest.download_file vm-100 /root/log /tmp/log username=root password='<pw>'
    """
    return c.download_file(
        __opts__,
        vm,
        src_path,
        dst_path,
        username=username,
        password=password,
        verify_ssl=verify_ssl,
        profile=profile,
    )


def list_files(vm, path, username=None, password=None, pattern=None, profile=None):
    """List files in a guest directory.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_guest.list_files vm-100 /root username=root password='<pw>'
    """
    return c.list_files(
        __opts__,
        vm,
        path,
        username=username,
        password=password,
        pattern=pattern,
        profile=profile,
    )


def delete_file(vm, path, username=None, password=None, profile=None):
    """Delete a file from the guest.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_guest.delete_file vm-100 /root/old.txt username=root password='<pw>'
    """
    return c.delete_file(__opts__, vm, path, username=username, password=password, profile=profile)


def make_directory(vm, path, username=None, password=None, create_parents=False, profile=None):
    """Make a directory in the guest (``create_parents=true`` for ``mkdir -p``).

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_guest.make_directory vm-100 /opt/app/etc create_parents=true username=root password='<pw>'
    """
    return c.make_directory(
        __opts__,
        vm,
        path,
        username=username,
        password=password,
        create_parents=create_parents,
        profile=profile,
    )


def delete_directory(vm, path, username=None, password=None, recursive=False, profile=None):
    """Delete a directory in the guest.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_guest.delete_directory vm-100 /tmp/build recursive=true username=root password='<pw>'
    """
    return c.delete_directory(
        __opts__,
        vm,
        path,
        username=username,
        password=password,
        recursive=recursive,
        profile=profile,
    )


def move_file(vm, src_path, dst_path, username=None, password=None, overwrite=False, profile=None):
    """Move or rename a file in the guest.

    CLI Example:

    .. code-block:: bash

        salt '*' vmware_vim_vm_guest.move_file vm-100 /root/a.txt /root/b.txt username=root password='<pw>'
    """
    return c.move_file(
        __opts__,
        vm,
        src_path,
        dst_path,
        username=username,
        password=password,
        overwrite=overwrite,
        profile=profile,
    )
