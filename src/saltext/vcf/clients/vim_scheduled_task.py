"""Scheduled tasks via ``ScheduledTaskManager`` (SOAP)."""

from pyVmomi import vim

from saltext.vcf.utils import vim as soap


def _stm(opts, profile=None):
    content = soap.content(opts, profile=profile)
    return content.scheduledTaskManager


def _find_task(opts, task_id_or_name, profile=None):
    stm = _stm(opts, profile=profile)
    for task in stm.scheduledTask or []:
        if task_id_or_name in (task._moId, task.info.name):  # noqa: SLF001
            return task
    raise LookupError(f"scheduled task {task_id_or_name!r} not found")


def _to_dict(task):
    info = task.info
    return {
        "id": task._moId,  # noqa: SLF001
        "name": info.name,
        "description": info.description,
        "enabled": bool(info.enabled),
        "entity": info.entity._moId if info.entity else None,  # noqa: SLF001
        "scheduler": type(info.scheduler).__name__ if info.scheduler else None,
        "last_modified_user": info.lastModifiedUser,
        "next_run_time": info.nextRunTime.isoformat() if info.nextRunTime else None,
        "state": str(info.state) if info.state else None,
    }


def list_(opts, entity=None, profile=None):
    """List scheduled tasks. If *entity* is given (moId), filter to tasks scoped to it."""
    stm = _stm(opts, profile=profile)
    if entity is not None:
        # Find the managed entity by moId
        content = soap.content(opts, profile=profile)
        ent = None
        for view_type in (vim.HostSystem, vim.VirtualMachine, vim.ClusterComputeResource):
            container = content.viewManager.CreateContainerView(
                content.rootFolder, [view_type], True
            )
            try:
                for e in container.view:
                    if e._moId == entity:  # noqa: SLF001
                        ent = e
                        break
            finally:
                container.Destroy()
            if ent is not None:
                break
        if ent is None:
            return []
        tasks = stm.RetrieveEntityScheduledTask(entity=ent)
    else:
        tasks = stm.scheduledTask or []
    return [_to_dict(t) for t in tasks]


def get(opts, task_id_or_name, profile=None):
    return _to_dict(_find_task(opts, task_id_or_name, profile=profile))


def get_or_none(opts, task_id_or_name, profile=None):
    try:
        return get(opts, task_id_or_name, profile=profile)
    except LookupError:
        return None


def create(opts, entity_moid, spec, profile=None):
    """Create a scheduled task. *spec* is a dict matching ``vim.scheduler.ScheduledTaskSpec``.

    Required keys: ``name``, ``description``, ``scheduler`` (dict with ``type`` like
    ``OnceTaskScheduler``, ``WeeklyTaskScheduler``, etc.), ``action`` (dict with
    ``method`` and ``arguments``). ``enabled`` defaults to True.
    """
    stm = _stm(opts, profile=profile)
    content = soap.content(opts, profile=profile)
    # Locate entity
    ent = None
    for view_type in (vim.HostSystem, vim.VirtualMachine, vim.ClusterComputeResource):
        container = content.viewManager.CreateContainerView(content.rootFolder, [view_type], True)
        try:
            for e in container.view:
                if e._moId == entity_moid:  # noqa: SLF001
                    ent = e
                    break
        finally:
            container.Destroy()
        if ent is not None:
            break
    if ent is None:
        raise LookupError(f"entity {entity_moid!r} not found")

    spec_obj = _build_task_spec(spec)
    new_task = stm.CreateScheduledTask(entity=ent, spec=spec_obj)
    return new_task._moId  # noqa: SLF001


def _build_task_spec(spec):
    task_spec = vim.scheduler.ScheduledTaskSpec()
    task_spec.name = spec["name"]
    task_spec.description = spec.get("description", "")
    task_spec.enabled = bool(spec.get("enabled", True))
    sched = spec.get("scheduler") or {}
    sched_type = sched.get("type", "OnceTaskScheduler")
    sched_cls = getattr(vim.scheduler, sched_type)
    sched_obj = sched_cls()
    for k, v in sched.items():
        if k == "type":
            continue
        setattr(sched_obj, k, v)
    task_spec.scheduler = sched_obj
    action = spec.get("action") or {}
    method_action = vim.action.MethodAction()
    method_action.name = action.get("method", "")
    method_action.argument = [
        vim.action.MethodActionArgument(value=v) for v in action.get("arguments", [])
    ]
    task_spec.action = method_action
    if "notification" in spec:
        task_spec.notification = spec["notification"]
    return task_spec


def reconfigure(opts, task_id_or_name, spec, profile=None):
    task = _find_task(opts, task_id_or_name, profile=profile)
    spec_obj = _build_task_spec(spec)
    task.ReconfigureScheduledTask(spec=spec_obj)
    return get(opts, task_id_or_name, profile=profile)


def delete(opts, task_id_or_name, profile=None):
    task = _find_task(opts, task_id_or_name, profile=profile)
    task.RemoveScheduledTask()
    return True


def run_now(opts, task_id_or_name, profile=None):
    task = _find_task(opts, task_id_or_name, profile=profile)
    task.RunScheduledTask()
    return True
