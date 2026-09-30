"""Execution module for ESXi firmware config backup / restore / reset (SOAP)."""

from saltext.vcf.clients import vim_host_firmware as c

__virtualname__ = "vcf_vim_host_firmware"


def __virtual__():
    return __virtualname__


def backup(host, push_file_to_master=False, profile=None):
    """Back up the ESXi host configuration to the minion cache dir.

    When *push_file_to_master*, the bundle is additionally pushed to the
    Salt master via ``cp.push``.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_firmware.backup esxi-01 push_file_to_master=true
    """
    ret = c.backup(__opts__, host, profile=profile)
    if push_file_to_master:
        file_name = next(iter(ret.values()))["file_name"]
        __salt__["cp.push"](file_name)
    return ret


def restore(host, source_file, saltenv=None, profile=None):
    """Restore the ESXi host configuration from *source_file*.

    *source_file* may be ``salt://``, ``http(s)://``, or a local path;
    ``salt://`` URIs are cached via ``cp.cache_file`` first. The restore
    is bracketed with maintenance mode.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_firmware.restore esxi-01 salt://vcf/esxi-config.tgz
    """
    if source_file.startswith("salt://"):
        source_file = __salt__["cp.cache_file"](source_file, saltenv=saltenv)
    return c.restore(__opts__, host, source_file, profile=profile)


def reset(host, profile=None):
    """Reset the ESXi host configuration to factory defaults.

    CLI Example:

    .. code-block:: bash

        salt '*' vcf_vim_host_firmware.reset esxi-01
    """
    return c.reset(__opts__, host, profile=profile)
