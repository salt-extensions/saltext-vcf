"""State module for vCenter's ESX Lifecycle Manager (vLCM) REST API.

Drives ESXi host patching for a vSphere cluster through the desired-image
workflow: configure and sync depots, define/commit a desired image, set the
cluster's apply policy, then check compliance and remediate against it.

Depot/image/policy specs default from pillar ``saltext.vcf:esxi_vlcm`` when
not passed explicitly — see :mod:`saltext.vcf.clients.esxi_vlcm` for the
underlying REST calls.

Example::

    patch-depot:
      vcf_esxi_vlcm.depot_configured:
        - depot_type: offline
        - location: http://repo.example.com/VMware-ESXi-9.2.0.0.25504872-depot.zip

    domain-c9:
      vcf_esxi_vlcm.image_configured:
        - image_spec:
            base_image:
              version: "9.2.0.0.25504872"
        - require:
          - vcf_esxi_vlcm: patch-depot
      vcf_esxi_vlcm.remediated:
        - require:
          - vcf_esxi_vlcm.image_configured: domain-c9
"""

import logging

from saltext.vcf.clients import esxi_vlcm as c

log = logging.getLogger(__name__)

__virtualname__ = "vcf_esxi_vlcm"


def __virtual__():
    return __virtualname__


def _ret(name):
    return {"name": name, "changes": {}, "result": True, "comment": ""}


def _fail(ret, exc):
    log.exception("vcf_esxi_vlcm state %r failed", ret["name"])
    ret["result"] = False
    ret["comment"] = str(exc)
    return ret


def _pillar_section(section):
    pillar = __opts__.get("pillar", {})  # noqa: F821
    root = pillar.get("saltext.vcf", {}) or {}
    return (root.get("esxi_vlcm", {}) or {}).get(section, {}) or {}


def _task_settings(kwargs):
    task = _pillar_section("task")
    timeout = kwargs.get("task_timeout", task.get("timeout", 14400))
    poll_interval = kwargs.get("task_poll_interval", task.get("poll_interval", 30))
    return timeout, poll_interval


def depot_configured(
    name,
    depot_type=None,
    location=None,
    source_type=None,
    enabled=True,
    description=None,
    ownerdata=None,
    profile=None,
    **kwargs,
):
    """Ensure a depot supplying ESXi update payloads is configured.

    *depot_type* is ``"offline"`` (a downloadable ZIP bundle at *location*,
    the common case) or ``"online"`` (a VMware/vendor update repository
    URL, also passed as *location*). Idempotent: no-op if a depot pointing
    at the same *location* already exists.
    """
    ret = _ret(name)
    depot_type = depot_type or "offline"
    cfg = _pillar_section(f"{depot_type}_depot")
    location = location or cfg.get("location")
    if not location:
        return _fail(
            ret,
            ValueError(
                "depot_configured requires 'location' "
                f"(or pillar esxi_vlcm:{depot_type}_depot:location)"
            ),
        )

    try:
        if depot_type == "online":
            existing = c.online_depot_list(__opts__, profile=profile) or []
        else:
            existing = c.offline_depot_list(__opts__, profile=profile) or []
        match = next((d for d in existing if d.get("location") == location), None)
    except Exception as exc:  # pylint: disable=broad-except
        return _fail(ret, exc)

    if match:
        ret["comment"] = f"{depot_type} depot {location!r} already configured"
        return ret

    if __opts__.get("test"):
        ret["result"] = None
        ret["comment"] = f"would create {depot_type} depot {location!r}"
        ret["changes"] = {"depot": location}
        return ret

    try:
        if depot_type == "online":
            c.online_depot_create(
                __opts__,
                {"location": location, "enabled": enabled},
                profile=profile,
            )
        else:
            timeout, poll_interval = _task_settings(kwargs)
            resp = c.offline_depot_create(
                __opts__,
                {
                    "source_type": source_type or cfg.get("source_type", "PULL"),
                    "location": location,
                    "description": description,
                    "ownerdata": ownerdata,
                },
                profile=profile,
            )
            c.wait_for_task(
                __opts__, resp, timeout=timeout, poll_interval=poll_interval, profile=profile
            )
    except Exception as exc:  # pylint: disable=broad-except
        return _fail(ret, exc)

    ret["changes"] = {"depot": location}
    ret["comment"] = f"{depot_type} depot {location!r} configured"
    return ret


def depot_synced(name, profile=None, **kwargs):
    """Trigger a depot sync so ESXi update payloads are up to date.

    Not idempotent — there's no cheap way to tell "already synced" apart
    from "sync never needed," so this always fires the sync action. Some
    vCenter builds don't expose the sync action at all (404); that's
    treated as a no-op, not a failure.
    """
    ret = _ret(name)
    if __opts__.get("test"):
        ret["result"] = None
        ret["comment"] = "would sync depots"
        return ret

    timeout, poll_interval = _task_settings(kwargs)
    try:
        resp = c.depot_sync(__opts__, profile=profile)
        if isinstance(resp, dict) and resp.get("skipped"):
            ret["comment"] = "depot sync not supported by this vCenter; skipped"
            return ret
        c.wait_for_task(
            __opts__, resp, timeout=timeout, poll_interval=poll_interval, profile=profile
        )
    except Exception as exc:  # pylint: disable=broad-except
        return _fail(ret, exc)

    ret["changes"] = {"synced": True}
    ret["comment"] = "depots synced"
    return ret


def _base_version(desired_image):
    return ((desired_image or {}).get("base_image") or {}).get("version")


def _first_draft_id(drafts):
    """Return the id of the first draft in a ``drafts_list`` response.

    vAPI "list" operations over map-typed data (drafts are keyed by draft
    id) commonly respond with a ``{"<id>": {...}}`` dict rather than a JSON
    list — the id is the dict *key*, not a field inside the value. Handles
    that shape as well as a list of ``{"id"/"draft_id"/"key": ...}`` objects
    or a bare list of id strings. Returns ``None`` if *drafts* is empty.
    """
    if isinstance(drafts, dict):
        if not drafts:
            return None
        return next(iter(drafts))
    if isinstance(drafts, list) and drafts:
        first = drafts[0]
        if isinstance(first, dict):
            return first.get("id") or first.get("draft_id") or first.get("key")
        return first
    return None


def image_configured(  # pylint: disable=too-many-return-statements,too-many-branches
    name,
    cluster_id=None,
    image_spec=None,
    display_name=None,
    existing_draft_action="delete",
    validate=True,
    commit=True,
    commit_message=None,
    profile=None,
    **kwargs,
):
    """Ensure the cluster's desired image matches *image_spec*.

    Idempotent on the committed image's ``base_image.version``. If a draft
    already exists on the cluster, *existing_draft_action* controls what
    happens: ``"fail"`` raises, ``"delete"`` (default) discards it and
    proceeds, ``"reuse"`` uses it as-is provided its base image version
    already matches *image_spec*.

    After commit, re-reads the desired image and verifies the version
    landed as requested — a commit that reports success but doesn't move
    the version is treated as a failure.
    """
    ret = _ret(name)
    cluster_id = cluster_id or name
    cfg = _pillar_section("image")
    image_spec = image_spec or cfg.get("spec")
    if not image_spec:
        return _fail(
            ret,
            ValueError(
                "image_configured requires 'image_spec' (or pillar esxi_vlcm:image:spec)"
            ),
        )
    desired_version = _base_version(image_spec)

    try:
        current = c.desired_image_get(__opts__, cluster_id, profile=profile)
    except Exception as exc:  # pylint: disable=broad-except
        return _fail(ret, exc)
    current_version = _base_version(current)
    if desired_version and current_version == desired_version:
        ret["comment"] = f"cluster {cluster_id} desired image already at {desired_version}"
        return ret

    try:
        drafts = c.drafts_list(__opts__, cluster_id, profile=profile) or []
    except Exception as exc:  # pylint: disable=broad-except
        return _fail(ret, exc)

    existing_id = _first_draft_id(drafts)
    draft_id = None
    if existing_id is not None:
        if existing_draft_action == "fail":
            return _fail(
                ret, RuntimeError(f"cluster {cluster_id} already has draft {existing_id!r}")
            )
        if existing_draft_action == "reuse":
            try:
                draft_doc = c.draft_get(__opts__, cluster_id, existing_id, profile=profile) or {}
            except Exception as exc:  # pylint: disable=broad-except
                return _fail(ret, exc)
            draft_version = _base_version(draft_doc.get("software_spec") or draft_doc)
            if desired_version and draft_version != desired_version:
                return _fail(
                    ret,
                    RuntimeError(
                        f"existing draft {existing_id!r} is version {draft_version!r}, "
                        f"not the requested {desired_version!r}"
                    ),
                )
            draft_id = existing_id
        else:  # "delete" (default)
            if __opts__.get("test"):
                ret["result"] = None
                ret["comment"] = (
                    f"would delete existing draft {existing_id!r} and import {desired_version}"
                )
                return ret
            try:
                c.draft_delete(__opts__, cluster_id, existing_id, profile=profile)
            except Exception as exc:  # pylint: disable=broad-except
                return _fail(ret, exc)

    if __opts__.get("test"):
        ret["result"] = None
        ret["comment"] = f"would set cluster {cluster_id} desired image to {desired_version}"
        ret["changes"] = {"base_image_version": {"old": current_version, "new": desired_version}}
        return ret

    timeout, poll_interval = _task_settings(kwargs)
    try:
        if draft_id is None:
            # Import always completes synchronously — no task to wait for.
            c.draft_import_software_spec(__opts__, cluster_id, image_spec, profile=profile)
            fresh = c.drafts_list(__opts__, cluster_id, profile=profile) or []
            draft_id = _first_draft_id(fresh)
        if draft_id is None:
            return _fail(
                ret,
                RuntimeError(f"could not determine draft id after import on cluster {cluster_id}"),
            )

        if validate:
            resp = c.draft_validate(__opts__, cluster_id, draft_id, profile=profile)
            c.wait_for_task(
                __opts__, resp, timeout=timeout, poll_interval=poll_interval, profile=profile
            )

        if commit:
            resp = c.draft_commit(
                __opts__,
                cluster_id,
                draft_id,
                message=commit_message or display_name,
                profile=profile,
            )
            c.wait_for_task(
                __opts__, resp, timeout=timeout, poll_interval=poll_interval, profile=profile
            )
            final = c.desired_image_get(__opts__, cluster_id, profile=profile)
            final_version = _base_version(final)
            if desired_version and final_version != desired_version:
                return _fail(
                    ret,
                    RuntimeError(
                        f"commit reported success but cluster {cluster_id} version is "
                        f"{final_version!r}, not the requested {desired_version!r}"
                    ),
                )
    except Exception as exc:  # pylint: disable=broad-except
        return _fail(ret, exc)

    ret["changes"] = {"base_image_version": {"old": current_version, "new": desired_version}}
    ret["comment"] = f"cluster {cluster_id} desired image set to {desired_version}"
    return ret


def policy_configured(name, cluster_id=None, policy_spec=None, profile=None, **kwargs):
    """Ensure the cluster's apply policy matches *policy_spec*.

    Idempotent on the subset of keys present in *policy_spec* — only those
    keys are compared against the current policy, so extra fields vCenter
    populates on its own don't cause a spurious "changed" every run.
    """
    ret = _ret(name)
    cluster_id = cluster_id or name
    policy_spec = policy_spec or _pillar_section("policy")
    if not policy_spec:
        return _fail(
            ret,
            ValueError("policy_configured requires 'policy_spec' (or pillar esxi_vlcm:policy)"),
        )

    try:
        current = c.apply_policy_get(__opts__, cluster_id, profile=profile) or {}
    except Exception as exc:  # pylint: disable=broad-except
        return _fail(ret, exc)

    diff = {k: v for k, v in policy_spec.items() if current.get(k) != v}
    if not diff:
        ret["comment"] = f"cluster {cluster_id} apply policy already matches"
        return ret

    if __opts__.get("test"):
        ret["result"] = None
        ret["comment"] = f"would update cluster {cluster_id} apply policy: {sorted(diff)}"
        ret["changes"] = diff
        return ret

    try:
        c.apply_policy_set(__opts__, cluster_id, policy_spec, profile=profile)
    except Exception as exc:  # pylint: disable=broad-except
        return _fail(ret, exc)

    ret["changes"] = diff
    ret["comment"] = f"cluster {cluster_id} apply policy updated"
    return ret


def _lifecycle_step(name, cluster_id, slug, label, client_fn, call_kwargs, kwargs, profile):
    ret = _ret(name)
    cluster_id = cluster_id or name
    if __opts__.get("test"):
        ret["result"] = None
        ret["comment"] = f"would {label} cluster {cluster_id}"
        return ret

    timeout, poll_interval = _task_settings(kwargs)
    try:
        resp = client_fn(__opts__, cluster_id, profile=profile, **call_kwargs)
        task = c.wait_for_task(
            __opts__, resp, timeout=timeout, poll_interval=poll_interval, profile=profile
        )
    except Exception as exc:  # pylint: disable=broad-except
        return _fail(ret, exc)

    ret["changes"] = {slug: task.get("status")}
    ret["comment"] = f"cluster {cluster_id} {label} complete"
    return ret


def compliance_checked(name, cluster_id=None, commit="1", hosts=None, profile=None, **kwargs):
    """Scan the cluster for compliance against its desired image.

    Always runs — there's no cheap "already compliant" signal to check
    beforehand; use :func:`reported` to inspect the result afterward.
    """
    return _lifecycle_step(
        name,
        cluster_id,
        "compliance_scan",
        "compliance scan",
        c.compliance_scan,
        {"commit": commit, "hosts": hosts},
        kwargs,
        profile,
    )


def prechecked(name, cluster_id=None, commit="1", profile=None, **kwargs):
    """Run remediation prechecks on the cluster. Always runs (see :func:`compliance_checked`)."""
    return _lifecycle_step(
        name, cluster_id, "precheck", "precheck", c.precheck, {"commit": commit}, kwargs, profile
    )


def staged(name, cluster_id=None, commit="1", hosts=None, profile=None, **kwargs):
    """Stage the desired image on cluster hosts. Always runs (see :func:`compliance_checked`)."""
    return _lifecycle_step(
        name,
        cluster_id,
        "stage",
        "stage",
        c.stage,
        {"commit": commit, "hosts": hosts},
        kwargs,
        profile,
    )


def remediated(name, cluster_id=None, accept_eula=True, profile=None, **kwargs):
    """Remediate (apply the desired image to) the cluster.

    Always runs (see :func:`compliance_checked`). Unlike
    :func:`compliance_checked`/:func:`staged`, remediation has no ``hosts``
    filter — it always targets the whole cluster.
    """
    ret = _ret(name)
    cluster_id = cluster_id or name
    if __opts__.get("test"):
        ret["result"] = None
        ret["comment"] = f"would remediate cluster {cluster_id}"
        return ret

    timeout, poll_interval = _task_settings(kwargs)
    try:
        resp = c.remediate(__opts__, cluster_id, accept_eula=accept_eula, profile=profile)
        task = c.wait_for_task(
            __opts__, resp, timeout=timeout, poll_interval=poll_interval, profile=profile
        )
    except Exception as exc:  # pylint: disable=broad-except
        return _fail(ret, exc)

    ret["changes"] = {"remediate": task.get("status")}
    ret["comment"] = f"cluster {cluster_id} remediated"
    return ret


def reported(name, cluster_id=None, profile=None):
    """Fetch the cluster's last check/apply-impact/apply reports.

    Always a no-op read (``changed=False``) — the reports are surfaced in
    ``comment`` only; use the corresponding
    :mod:`saltext.vcf.modules.vcf_esxi_vlcm` functions to consume the full
    payloads programmatically.
    """
    ret = _ret(name)
    cluster_id = cluster_id or name
    try:
        last_check = c.last_check_result(__opts__, cluster_id, profile=profile)
        apply_impact = c.apply_impact_report(__opts__, cluster_id, profile=profile)
        last_apply = c.last_apply_result(__opts__, cluster_id, profile=profile)
    except Exception as exc:  # pylint: disable=broad-except
        return _fail(ret, exc)

    ret["comment"] = (
        f"cluster {cluster_id}: last_check={'present' if last_check else 'none'}, "
        f"apply_impact={'present' if apply_impact else 'none'}, "
        f"last_apply={'present' if last_apply else 'none'}"
    )
    return ret
