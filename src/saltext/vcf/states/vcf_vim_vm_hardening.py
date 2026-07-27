"""
VM hardening state module for 912 Controls compliance.

Named, discoverable wrappers over the ``extraConfig`` (``advanced_settings``)
surface exposed by :mod:`saltext.vcf.states.vcf_vim_vm` /
:mod:`saltext.vcf.modules.vcf_vim_vm` so that a compliance SLS reads as
control names rather than opaque option-value dicts.

Each state reads the VM's current ``extraConfig`` via
``vcf_vim_vm.get_advanced_settings`` and only writes drifted keys via
``vcf_vim_vm.reconfigure(advanced_settings=...)`` -- the same underlying
plumbing already used for the raw dict form. Idempotent and honors
``test=True``.

Controls covered:

- ``console_options_locked`` -- 912 Controls: disable VM console
  copy/paste/GUI-options/disk-shrink/disk-wiper (isolation.tools.*).
- ``hgfs_disabled`` -- 912 Controls #19/#24/#25: disable the HGFS server.
- ``log_rotation_configured`` -- 912 Controls #18: cap VM log rotation.
"""

__virtualname__ = "vcf_vim_vm_hardening"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def _apply_extra_config(name, vm, desired, profile, ret):
    """Read current extraConfig; write only drifted keys.

    ``desired`` is a dict of ``{key: value}`` where every value is coerced
    to ``str`` (vSphere always returns extraConfig as strings).
    """
    desired = {k: str(v) for k, v in desired.items()}
    current = __salt__["vcf_vim_vm.get_advanced_settings"](vm, profile=profile)
    drift = {k: v for k, v in desired.items() if str(current.get(k)) != v}
    if not drift:
        ret["comment"] = f"VM {vm!r} already matches: {sorted(desired)}"
        return ret

    changes = {k: {"old": current.get(k), "new": v} for k, v in drift.items()}
    if __opts__["test"]:
        ret["result"] = None
        ret["comment"] = f"Would set {sorted(drift)} on VM {vm!r}"
        ret["changes"] = changes
        return ret

    __salt__["vcf_vim_vm.reconfigure"](vm, advanced_settings=drift, profile=profile)
    ret["changes"] = changes
    ret["comment"] = f"Set {sorted(drift)} on VM {vm!r}"
    return ret


# ---------------------------------------------------------------------------
# Console isolation options (copy/paste/GUI/disk-shrink/disk-wiper)
# ---------------------------------------------------------------------------


CONSOLE_LOCK_KEYS = (
    "isolation.tools.copy.disable",
    "isolation.tools.paste.disable",
    "isolation.tools.setGUIOptions.enable",
    "isolation.tools.diskShrink.disable",
    "isolation.tools.diskWiper.disable",
)


def console_options_locked(name, vm, profile=None):
    """Ensure the five isolation.tools console/disk keys are hardened.

    Sets ``isolation.tools.copy.disable``,
    ``isolation.tools.paste.disable``,
    ``isolation.tools.setGUIOptions.enable``,
    ``isolation.tools.diskShrink.disable``, and
    ``isolation.tools.diskWiper.disable`` all to ``"TRUE"`` on the target
    VM.

    Wraps the raw ``vcf_vim_vm.reconfigure`` ``advanced_settings=`` surface
    so compliance SLS reads as a named control rather than an opaque dict.
    """
    ret = _ret(name)
    desired = {k: "TRUE" for k in CONSOLE_LOCK_KEYS}
    return _apply_extra_config(name, vm, desired, profile, ret)


# ---------------------------------------------------------------------------
# HGFS server disable (912 Controls #19/#24/#25)
# ---------------------------------------------------------------------------


def hgfs_disabled(name, vm, profile=None):
    """Ensure ``isolation.tools.hgfsServerSet.disable`` is ``"TRUE"`` on *vm*.

    Disables the HGFS (Host-Guest File System) server, addressing 912
    Controls guidance items #19, #24 and #25 (unauthorized shared-folder
    channels between guest and host).
    """
    ret = _ret(name)
    desired = {"isolation.tools.hgfsServerSet.disable": "TRUE"}
    return _apply_extra_config(name, vm, desired, profile, ret)


# ---------------------------------------------------------------------------
# Log rotation (912 Controls #18)
# ---------------------------------------------------------------------------


def log_rotation_configured(name, vm, keep_old=10, rotate_size=1024000, profile=None):
    """Ensure VM log rotation caps are set.

    Sets ``log.keepOld`` (default ``10``) and ``log.rotateSize`` (default
    ``1024000`` bytes) on the target VM. Prevents runaway ``vmware.log``
    growth per 912 Controls #18.
    """
    ret = _ret(name)
    desired = {
        "log.keepOld": str(int(keep_old)),
        "log.rotateSize": str(int(rotate_size)),
    }
    return _apply_extra_config(name, vm, desired, profile, ret)
