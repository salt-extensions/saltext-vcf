"""State module for ESXi ``/etc/rc.local.d/local.sh`` custom boot commands."""

from saltext.vcf.clients import esxi_localsh as c

__virtualname__ = "vcf_esxi_localsh"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def managed(name, features, execute=True, profile=None):
    """Ensure ESXi's persistent ``local.sh`` contains the given *features*
    (a ``{label: shell_command}`` dict, one line per entry).

    *name* is descriptive only. Unless *execute* is ``False``, the script
    is also written to the exec path and run immediately, so the change
    takes effect without waiting for the next reboot.

    A falsy *features* is a no-op, matching the Ansible role's own
    ``when: esxi_localsh_features is defined and != ""`` guard -- nothing
    is written or run when there's nothing to configure.
    """
    ret = _ret(name)
    if not features:
        ret["comment"] = "no local.sh features given; nothing to do"
        return ret

    content = c.render(features)
    current = c.get(__opts__, profile=profile)
    if current == content:
        ret["comment"] = "local.sh already matches"
        return ret
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = "local.sh would be updated"
        return ret
    c.apply(__opts__, features, execute=execute, profile=profile)
    ret["changes"] = {"old": current, "new": content}
    ret["comment"] = "local.sh updated" + (" and executed" if execute else "")
    return ret
