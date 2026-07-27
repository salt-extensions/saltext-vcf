"""State module for VCF Automation lifecycle / patch-baseline enforcement.

Drives VCFA's LCM patch surface (:mod:`saltext.vcf.clients.vcfa_lifecycle`)
so that a product's installed patches stay within an operator-approved
baseline.

Two shapes ship here:

* :func:`patch_present` — enforcement: applies a patch when the product
  is not currently on an allowed version. Requires VCFA's LCM upgrade
  submission endpoint (``POST /lcm/api/upgrades``) to be live; on
  builds where it isn't, the state falls back to compliance-check
  behaviour and emits a failure describing what needs to happen
  manually.
* :func:`baseline_check` — read-only compliance check: compares the
  currently installed patches for a product against a caller-supplied
  allowed list (typically sourced from an ITIL policy / TSC baseline
  document) and returns compliant / non-compliant without ever
  changing state on the appliance.

Neither state expects VCFA to itself store the "approved baseline" —
that concept is external to LCM. The allowed list is passed in by the
caller (state ``allowed_versions=`` argument) or read from pillar at
``saltext.vcf:vcfa_lifecycle:baselines:<product_id>``.

Example — enforce that a product stays on one of two approved patches::

    vcfa-automation-service-baseline:
      vcf_vcfa_lifecycle.patch_present:
        - product: automation-service
        - allowed_versions:
          - 9.0.1.2
          - 9.0.1.3
        - target_version: 9.0.1.3   # optional; picks highest allowed if omitted

Example — non-enforcing check::

    vcfa-baseline-audit:
      vcf_vcfa_lifecycle.baseline_check:
        - product: automation-service
        - allowed_versions:
          - 9.0.1.2
          - 9.0.1.3
"""

import logging

from saltext.vcf.clients import vcfa_lifecycle as c

log = logging.getLogger(__name__)

__virtualname__ = "vcf_vcfa_lifecycle"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def _fail(ret, exc):
    log.exception("vcf_vcfa_lifecycle state %r failed", ret["name"])
    ret["result"] = False
    ret["comment"] = str(exc)
    return ret


def _cfg():
    pillar = __opts__.get("pillar", {})  # noqa: F821
    root = pillar.get("saltext.vcf", {}) or {}
    return root.get("vcfa_lifecycle", {}) or {}


def _resolve_allowed(product, allowed_versions):
    """Return the effective allowed list — explicit, else pillar baseline map."""
    if allowed_versions:
        return list(allowed_versions)
    cfg = _cfg()
    baselines = cfg.get("baselines", {}) or {}
    return list(baselines.get(product, []) or [])


def _installed_summary(opts, product, profile):
    entries = c.installed_patches(opts, product, profile=profile)
    versions = [c.resolve_patch_version(e) for e in entries]
    return entries, [v for v in versions if v]


def baseline_check(name, product=None, allowed_versions=None, profile=None):
    """Assert that every installed patch for *product* is in *allowed_versions*.

    Read-only — never triggers a patch install. Failure mode is a
    non-truthy ``result`` so orchestration can gate on it.

    *product* defaults to *name* if unset. *allowed_versions* defaults
    to the pillar entry at
    ``saltext.vcf:vcfa_lifecycle:baselines:<product>``.
    """
    ret = _ret(name)
    product = product or name
    allowed = _resolve_allowed(product, allowed_versions)
    if not allowed:
        return _fail(
            ret,
            ValueError(
                "baseline_check requires 'allowed_versions' "
                "(or pillar vcfa_lifecycle:baselines:<product>)"
            ),
        )

    try:
        entries, installed_versions = _installed_summary(__opts__, product, profile)
    except Exception as exc:  # pylint: disable=broad-except
        return _fail(ret, exc)

    out_of_baseline = []
    in_baseline = []
    for entry in entries:
        version = c.resolve_patch_version(entry)
        if version is None:
            continue
        if c.is_patch_allowed(entry, allowed):
            in_baseline.append(version)
        else:
            out_of_baseline.append(version)

    if not installed_versions:
        ret["result"] = False
        ret["comment"] = (
            f"{product!r} reports no installed patches — cannot determine baseline compliance"
        )
        ret["changes"] = {"allowed": allowed, "installed": []}
        return ret

    if out_of_baseline:
        ret["result"] = False
        ret["comment"] = (
            f"{product!r} out of baseline: installed {out_of_baseline} "
            f"not in allowed {allowed}"
        )
    else:
        ret["comment"] = (
            f"{product!r} within baseline: installed {installed_versions} "
            f"⊆ allowed {allowed}"
        )
    ret["changes"] = {}
    ret["pchanges"] = {
        "installed": installed_versions,
        "in_baseline": in_baseline,
        "out_of_baseline": out_of_baseline,
        "allowed": allowed,
    }
    return ret


def _pick_target(allowed, available_entries):
    """Choose the target patch version: the highest allowed version that is available.

    Falls back to the last allowed entry if none of them appear in the
    available list (so the state at least surfaces a coherent request
    to the LCM controller, even if that call itself later 404s).
    """
    available_map = {}
    for entry in available_entries:
        for field in c._patch_version_fields(entry):  # pylint: disable=protected-access
            available_map.setdefault(field, entry)

    matches = [v for v in allowed if str(v) in available_map]
    if matches:
        # Prefer the last matching entry — allowed lists are typically
        # ordered oldest-to-newest, so "highest allowed" == last-match.
        return matches[-1]
    return allowed[-1] if allowed else None


def patch_present(
    name,
    product=None,
    allowed_versions=None,
    target_version=None,
    profile=None,
):
    """Ensure *product* is running one of *allowed_versions*.

    Idempotent: no-op when at least one installed patch already
    matches the allowed list. Otherwise submits an LCM patch-install
    upgrade for *target_version* (or the last entry of *allowed_versions*
    that is currently available, or the last allowed entry if no
    availability data is present).

    Notes:

    * Does **not** poll the resulting upgrade to completion. VCFA
      upgrades can take an hour+; the caller should chain a
      :func:`vcf_vcfa_lifecycle.wait_for_upgrade
      <saltext.vcf.modules.vcf_vcfa_lifecycle.wait_for_upgrade>`
      exec-module call in a separate state or orchestration if it
      wants to block on the outcome.
    * Emits a soft failure (result=False, comment describes the
      situation) rather than raising if the LCM upgrade endpoint 404s
      — some VCFA builds gate ``/lcm/api/upgrades`` behind a feature
      flag that operators must enable out-of-band.
    """
    ret = _ret(name)
    product = product or name
    allowed = _resolve_allowed(product, allowed_versions)
    if not allowed:
        return _fail(
            ret,
            ValueError(
                "patch_present requires 'allowed_versions' "
                "(or pillar vcfa_lifecycle:baselines:<product>)"
            ),
        )

    try:
        installed_entries, installed_versions = _installed_summary(
            __opts__, product, profile
        )
    except Exception as exc:  # pylint: disable=broad-except
        return _fail(ret, exc)

    if any(c.is_patch_allowed(entry, allowed) for entry in installed_entries):
        ret["comment"] = (
            f"{product!r} already at allowed patch level "
            f"(installed={installed_versions}, allowed={allowed})"
        )
        return ret

    try:
        available_entries = c.available_patches(__opts__, product, profile=profile)
    except Exception as exc:  # pylint: disable=broad-except
        return _fail(ret, exc)

    target = target_version or _pick_target(allowed, available_entries)
    if not target:
        return _fail(
            ret,
            RuntimeError(
                f"cannot resolve a target patch version for {product!r} "
                f"(allowed={allowed}, available={[c.resolve_patch_version(e) for e in available_entries]})"
            ),
        )

    if __opts__.get("test"):
        ret["result"] = None
        ret["comment"] = (
            f"would apply patch {target!r} to {product!r} "
            f"(installed={installed_versions}, allowed={allowed})"
        )
        ret["changes"] = {"planned": {"product": product, "target": target}}
        return ret

    try:
        upgrade = c.apply_patch(__opts__, product, target, profile=profile)
    except Exception as exc:  # pylint: disable=broad-except
        # Distinguish "LCM upgrade endpoint not present on this build" from
        # a real submission failure — the former is common on VCFA builds
        # that ship the read side but not the write side.
        resp = getattr(exc, "response", None)
        status = getattr(resp, "status_code", None)
        if status == 404:
            ret["result"] = False
            ret["comment"] = (
                f"{product!r} out of baseline (installed={installed_versions}, "
                f"allowed={allowed}) — LCM upgrade endpoint returned 404, "
                f"remediation must be driven out-of-band"
            )
            ret["changes"] = {}
            ret["pchanges"] = {"needed": target, "installed": installed_versions}
            return ret
        return _fail(ret, exc)

    upgrade_id = (
        upgrade.get("id") if isinstance(upgrade, dict) else None
    )
    ret["comment"] = (
        f"submitted patch-install upgrade for {product!r} → {target!r} "
        f"(upgrade id: {upgrade_id!r})"
    )
    ret["changes"] = {
        "product": product,
        "target": target,
        "upgrade": upgrade,
    }
    return ret
